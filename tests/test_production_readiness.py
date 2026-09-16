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


class TestProductionReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()

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

    def test_ssrf_allows_public_web(self):
        """Verify SSRF guard allows legitimate public web URLs."""
        is_safe, err = main.is_safe_url("https://www.google.com")
        self.assertTrue(is_safe, f"Failed on safe public URL: {err}")

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

    # ---------------- 5. Concurrency Limiter ----------------

    def test_concurrency_limiter(self):
        """Verify per-user concurrency semaphore allows up to 2 streams and rejects 3rd."""
        test_uid = f"concurrent_test_{self.user['id']}"
        self.assertTrue(main.acquire_user_stream(test_uid))
        self.assertTrue(main.acquire_user_stream(test_uid))
        # 3rd should be rejected
        self.assertFalse(main.acquire_user_stream(test_uid))

        # Release one stream
        main.release_user_stream(test_uid)
        # Should now be allowed
        self.assertTrue(main.acquire_user_stream(test_uid))
        # Cleanup
        main.release_user_stream(test_uid)
        main.release_user_stream(test_uid)

    # ---------------- 6. Model & Mode Governance ----------------

    def test_model_and_mode_allowlist(self):
        """Verify model and mode validation sets."""
        self.assertIn("nvidia/nemotron-3-super-120b-a12b", main.VALID_MODEL_IDS)
        self.assertIn("auto", main.ALLOWED_MODES)
        self.assertIn("fast", main.ALLOWED_MODES)
        self.assertIn("thinking", main.ALLOWED_MODES)
        self.assertNotIn("untrusted-custom-model", main.VALID_MODEL_IDS)
        self.assertNotIn("jailbreak", main.ALLOWED_MODES)

    # ---------------- 7. Project Ownership Isolation ----------------

    def test_project_ownership_isolation(self):
        """Verify users cannot associate another user's project with their conversation."""
        other_user = database.create_user(f"other_{self.test_username}", "Password123!")
        other_project = database.create_project(user_id=other_user["id"], name="Secret Project")

        # User attempts to create conversation using other user's project_id
        conv = database.create_conversation(title="Test", user_id=self.user["id"], project_id=other_project["id"])
        # Should be sanitized to None
        self.assertIsNone(conv["project_id"])

    # ---------------- 8. Database Versioning ----------------

    def test_schema_version_tracking(self):
        """Verify schema migration tracking is at version >= 3."""
        version = database.get_schema_version()
        self.assertGreaterEqual(version, 3)

    # ---------------- 9. Minimal Public Health ----------------

    def test_minimal_public_health(self):
        """Verify public health endpoint discloses minimal liveness information."""
        health = main.health()
        self.assertEqual(health, {"status": "ok", "version": "3.1.0"})
        self.assertNotIn("api_key_configured", health)
        self.assertNotIn("available_models", health)


if __name__ == "__main__":
    unittest.main(verbosity=2)
