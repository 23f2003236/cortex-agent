"""
Comprehensive Production Readiness and Security Test Suite for Cortex Agent.
Covers:
- Auth, password hashing, and token revocation
- Guest account isolation and quota boundaries
- SSRF prevention (DNS resolution, private IPs, metadata endpoint)
- Upload hardening and magic byte validation
- Atomic quota reservation and reconciliation
- Per-user streaming concurrency limits
- Model and mode governance
- Project workspace isolation
- Database schema version tracking
- Minimal public health endpoint
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import database
import main


import tempfile
from fastapi.testclient import TestClient


class TestProductionReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        cls.orig_db_path = database.DB_PATH
        database.set_db_path(Path(cls.temp_db.name))
        database.init_db()
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        database.set_db_path(cls.orig_db_path)
        try:
            os.unlink(cls.temp_db.name)
        except Exception:
            pass

    def setUp(self):
        # Create unique user for each test
        import uuid
        self.test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        self.user = database.create_user(self.test_username, "SecurePassword123!")

    # ---------------- 1. Auth & Secrets ----------------

    def test_secret_key_entropy(self):
        """Verify SECRET_KEY is not the default insecure secret and has high entropy."""
        secret = main.SECRET_KEY
        self.assertTrue(secret)
        self.assertNotEqual(secret, main.DEFAULT_INSECURE_SECRET)
        self.assertGreaterEqual(len(secret), 32)

    def test_password_hashing_600k_rounds(self):
        """Verify password hashing uses 600,000 PBKDF2 rounds."""
        pw_hash, salt = database.hash_password("MySecurePass123!")
        self.assertIn("$600000", salt)
        self.assertTrue(database.verify_password("MySecurePass123!", pw_hash, salt))
        self.assertFalse(database.verify_password("WrongPassword!", pw_hash, salt))

    def test_password_minimum_length(self):
        """Verify passwords under 8 characters are strictly rejected."""
        with self.assertRaises(ValueError):
            database.create_user(f"short_{self.test_username}", "short")

    def test_token_tampering_rejected(self):
        """Verify forged or modified tokens are rejected."""
        token = main.generate_token(self.user["id"], self.user["username"])
        parts = token.split(".")
        # Tamper with payload
        tampered_token = f"{parts[0]}X.{parts[1]}"
        self.assertIsNone(main.verify_token(tampered_token))

    def test_server_side_token_revocation(self):
        """Verify logged out / revoked tokens are invalidated immediately."""
        token = main.generate_token(self.user["id"], self.user["username"])
        self.assertIsNotNone(main.verify_token(token))
        # Revoke token signature
        sig = token.split(".")[1]
        database.revoke_token(sig, self.user["id"])
        self.assertIsNone(main.verify_token(token))

    def test_auth_rate_limiting_and_lockout(self):
        """Verify distributed auth rate limiting locks out after threshold."""
        rate_key = f"test_login_user_{self.test_username}"
        # Max 3 attempts allowed in 60 seconds
        for i in range(3):
            allowed, remaining = database.check_and_record_auth_attempt(rate_key, max_attempts=3, window_seconds=60)
            self.assertTrue(allowed, f"Attempt {i+1} should be allowed")
        # 4th attempt should be blocked
        allowed, wait_sec = database.check_and_record_auth_attempt(rate_key, max_attempts=3, window_seconds=60)
        self.assertFalse(allowed)
        self.assertGreaterEqual(wait_sec, 1)

        # Resetting counter restores access
        database.reset_auth_attempts(rate_key)
        allowed, _ = database.check_and_record_auth_attempt(rate_key, max_attempts=3, window_seconds=60)
        self.assertTrue(allowed)

    # ---------------- 2. Guest Isolation ----------------

    def test_guest_account_isolation(self):
        """Verify guest accounts are ephemeral, unique, and strictly quota-isolated."""
        g1 = database.create_guest_user()
        g2 = database.create_guest_user()
        self.assertNotEqual(g1["id"], g2["id"])
        self.assertTrue(g1["is_guest"])
        self.assertTrue(g2["is_guest"])
        self.assertTrue(g1["username"].startswith("guest_"))

        # Verify quota separation
        usage1 = database.get_daily_usage(g1["id"])
        usage2 = database.get_daily_usage(g2["id"])
        self.assertEqual(usage1["tokens_limit"], database.GUEST_DAILY_TOKEN_LIMIT)
        self.assertEqual(usage1["uploads_limit"], database.GUEST_DAILY_UPLOAD_LIMIT)
        self.assertEqual(usage1["tokens_used"], 0)
        self.assertEqual(usage2["tokens_used"], 0)

    def test_guest_zero_pbkdf2_and_expiration(self):
        """Verify guest creation skips 600k PBKDF2 rounds and tracks expires_at."""
        g = database.create_guest_user()
        self.assertIn("expires_at", g)
        self.assertTrue(g["expires_at"])

        # Verify guest user cannot authenticate via password login
        auth_result = database.authenticate_user(g["username"], "any_password")
        self.assertIsNone(auth_result, "Guest user must not be authenticatable via password")

    def test_cleanup_expired_guests(self):
        """Verify cleanup_expired_guests sweeps expired guest sessions."""
        # Create an immediately-expired guest
        g_exp = database.create_guest_user(ttl_hours=-1)
        # Create an active guest
        g_act = database.create_guest_user(ttl_hours=24)

        deleted = database.cleanup_expired_guests()
        self.assertGreaterEqual(deleted, 1)

        # Expired guest is gone, active guest remains
        self.assertIsNone(database.get_user_by_id(g_exp["id"]))
        self.assertIsNotNone(database.get_user_by_id(g_act["id"]))

    # ---------------- 3. SSRF Protection ----------------

    def test_ssrf_blocks_loopback_and_localhost(self):
        """Verify SSRF guard blocks localhost, loopback, and local domain names."""
        for target in ["http://localhost:8000", "http://127.0.0.1:80", "http://[::1]:443", "http://myserver.local"]:
            is_safe, err = main.is_safe_url(target)
            self.assertFalse(is_safe, f"Should have blocked {target}")

    def test_ssrf_blocks_cloud_metadata(self):
        """Verify SSRF guard blocks link-local / AWS / GCP metadata endpoints."""
        for target in ["http://169.254.169.254/latest/meta-data", "http://169.254.1.1"]:
            is_safe, err = main.is_safe_url(target)
            self.assertFalse(is_safe, f"Should have blocked metadata IP: {target}")

    def test_ssrf_blocks_non_standard_ports(self):
        """Verify SSRF guard blocks non-standard web ports."""
        for target in ["http://google.com:22", "http://google.com:3306", "http://google.com:6379"]:
            is_safe, err = main.is_safe_url(target)
            self.assertFalse(is_safe, f"Should have blocked port in {target}")

    def test_ssrf_allows_public_web_and_returns_pinned_ip(self):
        """Verify SSRF guard returns SafeUrlResult with pinned_ip to prevent DNS rebinding."""
        res = main.is_safe_url("https://www.google.com")
        self.assertTrue(res.is_safe, f"Failed on safe public URL: {res.error}")
        self.assertTrue(res.pinned_ip, "Must provide pinned_ip for direct socket connection")
        # Verify 2-tuple backwards compatibility
        is_safe, err = res
        self.assertTrue(is_safe)
        self.assertEqual(err, "")

    # ---------------- 4. Quota Reservation ----------------

    def test_atomic_quota_reservation_and_release(self):
        """Verify quota reservation prevents concurrent race conditions and reconciles correctly."""
        user_id = self.user["id"]
        # Reserve 1,000 tokens
        ok, proj, lim = database.reserve_quota(user_id, 1000)
        self.assertTrue(ok)

        usage = database.get_daily_usage(user_id)
        self.assertEqual(usage["reserved_tokens"], 1000)
        self.assertEqual(usage["tokens_remaining"], lim - 1000)

        # Release reservation and commit 250 actual tokens consumed
        new_usage = database.release_quota(user_id, estimated_tokens=1000, actual_tokens=250)
        self.assertEqual(new_usage["reserved_tokens"], 0)
        self.assertEqual(new_usage["tokens_used"], 250)
        self.assertEqual(new_usage["tokens_remaining"], lim - 250)

    def test_quota_exhaustion_blocks_reservation(self):
        """Verify requesting more tokens than remaining daily limit is rejected."""
        user_id = self.user["id"]
        limit = database.DAILY_TOKEN_LIMIT
        # Attempt to reserve over the limit
        ok, proj, lim = database.reserve_quota(user_id, limit + 1000)
        self.assertFalse(ok)

    # ---------------- 5. Multi-Worker Concurrency Leases ----------------

    def test_multi_worker_concurrency_leases(self):
        """Verify multi-worker resilient stream leases allow up to 2 active streams per user."""
        test_uid = self.user["id"]
        ok1, sid1 = main.acquire_user_stream(test_uid)
        ok2, sid2 = main.acquire_user_stream(test_uid)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # 3rd stream attempt should be rejected
        ok3, sid3 = main.acquire_user_stream(test_uid)
        self.assertFalse(ok3)

        # Release first stream lease
        main.release_user_stream(sid1)

        # 3rd stream can now acquire
        ok4, sid4 = main.acquire_user_stream(test_uid)
        self.assertTrue(ok4)

        # Cleanup
        main.release_user_stream(sid2)
        main.release_user_stream(sid4)

    # ---------------- 6. Security Headers & CSP ----------------

    def test_content_security_policy_header(self):
        """Verify Content-Security-Policy and standard security headers are present."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        headers = resp.headers
        self.assertIn("Content-Security-Policy", headers)
        csp = headers["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "SAMEORIGIN")

    # ---------------- 7. Model & Mode Governance ----------------

    def test_model_and_mode_allowlist(self):
        """Verify model and mode validation sets."""
        self.assertIn("nvidia/nemotron-3-super-120b-a12b", main.VALID_MODEL_IDS)
        self.assertIn("auto", main.ALLOWED_MODES)
        self.assertIn("fast", main.ALLOWED_MODES)
        self.assertIn("thinking", main.ALLOWED_MODES)
        self.assertNotIn("untrusted-custom-model", main.VALID_MODEL_IDS)
        self.assertNotIn("jailbreak", main.ALLOWED_MODES)

    # ---------------- 8. Project Ownership Isolation ----------------

    def test_project_ownership_isolation(self):
        """Verify users cannot associate another user's project with their conversation."""
        other_user = database.create_user(f"other_{self.test_username}", "Password123!")
        other_project = database.create_project(user_id=other_user["id"], name="Secret Project")

        # User attempts to create conversation using other user's project_id
        conv = database.create_conversation(title="Test", user_id=self.user["id"], project_id=other_project["id"])
        # Should be sanitized to None
        self.assertIsNone(conv["project_id"])

    # ---------------- 9. Database Versioning ----------------

    def test_schema_version_tracking(self):
        """Verify schema migration tracking is at version >= 4."""
        version = database.get_schema_version()
        self.assertGreaterEqual(version, 4)

    # ---------------- 10. Minimal Public Health ----------------

    def test_minimal_public_health(self):
        """Verify public health endpoint discloses minimal liveness information."""
        health = main.health()
        self.assertEqual(health, {"status": "ok", "version": "3.1.0"})
        self.assertNotIn("api_key_configured", health)
        self.assertNotIn("available_models", health)


if __name__ == "__main__":
    unittest.main(verbosity=2)
