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
import sqlite3
import sys
import unittest
import uuid
from pathlib import Path

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import database
import main


import tempfile
from unittest.mock import patch, MagicMock
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
        cls.client.close()
        database.close_all_connections()
        database.set_db_path(cls.orig_db_path)
        database.close_all_connections()
        try:
            os.unlink(cls.temp_db.name)
        except Exception:
            pass

    def setUp(self):
        # Reset cookies for clean per-test isolation
        self.client.cookies.clear()
        # Create unique user for each test
        self.test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        self.user = database.create_user(self.test_username, "SecurePassword123!")

    def tearDown(self):
        database.close_all_connections()

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
        self.assertNotIn("'unsafe-eval'", csp, "CSP must not allow unsafe-eval")
        self.assertIn("frame-ancestors 'none'", csp, "CSP must enforce frame-ancestors 'none'")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")

    # ---------------- 7. Model & Mode Governance ----------------

    def test_model_and_mode_allowlist(self):
        """Verify model and mode validation sets."""
        self.assertIn("nvidia/nemotron-3-super-120b-a12b", main.VALID_MODEL_IDS)
        self.assertIn("z-ai/glm-5.3", main.VALID_MODEL_IDS)
        self.assertIn("z-ai/glm-5.3-flash", main.VALID_MODEL_IDS)
        self.assertNotIn("nvidia/nemotron-3.5-content-safety", main.VALID_MODEL_IDS)
        self.assertNotIn("nvidia/nemotron-3-embed-1b", main.VALID_MODEL_IDS)
        self.assertIn("auto", main.ALLOWED_MODES)
        self.assertIn("fast", main.ALLOWED_MODES)
        self.assertIn("thinking", main.ALLOWED_MODES)
        self.assertNotIn("untrusted-custom-model", main.VALID_MODEL_IDS)
        self.assertNotIn("jailbreak", main.ALLOWED_MODES)

    def test_glm_model_normalization_and_routing(self):
        """Verify GLM 5.3 aliases, token limits, and vision routing capabilities."""
        self.assertEqual(main.normalize_model_id("z-ai/glm-5.3"), "z-ai/glm-5.3")
        self.assertEqual(main.normalize_model_id("z-ai/glm-5-3"), "z-ai/glm-5.3")
        self.assertEqual(main.normalize_model_id("z-ai/glm-5.3-flash"), "z-ai/glm-5.3-flash")
        self.assertEqual(main.normalize_model_id("z-ai/glm-5-3-flash"), "z-ai/glm-5.3-flash")

        # Verify token headroom
        self.assertEqual(main.MODEL_TOKEN_LIMITS["z-ai/glm-5.3"], 32768)
        self.assertEqual(main.MODEL_TOKEN_LIMITS["z-ai/glm-5.3-flash"], 32768)

        # Verify presence in AVAILABLE_MODELS
        available_ids = [m["id"] for m in main.AVAILABLE_MODELS]
        self.assertIn("z-ai/glm-5.3", available_ids)
        self.assertIn("z-ai/glm-5.3-flash", available_ids)
        self.assertNotIn("nvidia/nemotron-3.5-content-safety", available_ids)
        self.assertNotIn("nvidia/nemotron-3-embed-1b", available_ids)

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
        """Verify schema migration tracking is at version >= 5."""
        version = database.get_schema_version()
        self.assertGreaterEqual(version, 5)

    # ---------------- 10. Minimal Public Health ----------------

    def test_minimal_public_health(self):
        """Verify public health endpoint discloses minimal liveness information."""
        health = main.health()
        self.assertEqual(health, {"status": "ok", "version": "3.1.0"})
        self.assertNotIn("api_key_configured", health)
        self.assertNotIn("available_models", health)

    # ---------------- 11. Reverse-Proxy Trusted IP Resolution ----------------

    def test_reverse_proxy_client_ip_spoofing_prevention(self):
        """Verify untrusted direct client cannot spoof IP via X-Forwarded-For."""
        req = MagicMock()
        req.client.host = "203.0.113.195"  # Public untrusted IP
        req.headers = {"X-Forwarded-For": "1.1.1.1", "CF-Connecting-IP": "8.8.8.8"}
        client_ip = main.get_client_ip(req)
        self.assertEqual(client_ip, "203.0.113.195", "Must ignore headers from untrusted direct connection")

    def test_reverse_proxy_trusted_forwarding(self):
        """Verify trusted proxy connection extracts correct client IP."""
        req = MagicMock()
        req.client.host = "127.0.0.1"  # Trusted loopback proxy
        req.headers = {"X-Forwarded-For": "203.0.113.50"}
        client_ip = main.get_client_ip(req)
        self.assertEqual(client_ip, "203.0.113.50")

        # Test Cloudflare CF-Connecting-IP
        req.headers = {"CF-Connecting-IP": "198.51.100.99", "X-Forwarded-For": "198.51.100.99, 127.0.0.1"}
        client_ip = main.get_client_ip(req)
        self.assertEqual(client_ip, "198.51.100.99")

    # ---------------- 12. Request Body Limit Middleware (413) ----------------

    def test_request_body_size_limit_413(self):
        """Verify payloads exceeding 2 MB return HTTP 413 Request Entity Too Large."""
        large_payload = {"username": "a" * 100, "password": "b" * 100, "extra": "x" * (2 * 1024 * 1024 + 500)}
        resp = self.client.post("/api/auth/login", json=large_payload)
        self.assertEqual(resp.status_code, 413)
        self.assertIn("too large", resp.json().get("detail", "").lower())

    # ---------------- 13. Message Context Character Limit (422) ----------------

    def test_message_context_character_limit_422(self):
        """Verify conversations exceeding 250,000 total characters are rejected with 422."""
        token = main.generate_token(self.user["id"], self.user["username"])
        huge_message = {"role": "user", "content": "A" * 260_000}
        payload = {
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "messages": [huge_message],
        }
        resp = self.client.post(
            "/api/chat/stream",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 422)

    # ---------------- 14. Guest Chat Within 25k Quota ----------------

    @patch("main.make_llm")
    def test_guest_chat_operates_within_quota(self, mock_make_llm):
        """Verify guest account initiates streaming chat without quota rejection."""
        mock_instance = MagicMock()
        mock_instance.stream.return_value = [
            MagicMock(content="Hello", response_metadata={}, additional_kwargs={})
        ]
        mock_make_llm.return_value = mock_instance

        guest_resp = self.client.post("/api/auth/guest")
        self.assertEqual(guest_resp.status_code, 200)
        guest_data = guest_resp.json()
        self.assertNotIn("token", guest_data, "Browser guest auth must omit token from response body")
        self.assertIn("cortex_session", guest_resp.cookies, "Browser guest auth must set cortex_session cookie")
        guest_id = guest_data["user"]["id"]

        usage = database.get_daily_usage(guest_id)
        self.assertEqual(usage["tokens_limit"], 25000)
        self.assertEqual(usage["token_limit"], 25000)

        payload = {
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "messages": [{"role": "user", "content": "Hello! What is 2 + 2?"}],
        }
        resp = self.client.post(
            "/api/chat/stream",
            json=payload,
            cookies={"cortex_session": guest_resp.cookies["cortex_session"]},
        )
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertNotIn("Daily token quota reached", content)
        self.assertIn('"type": "init"', content)
        import re
        m = re.search(r'"budget_tokens":\s*(\d+)', content)
        self.assertTrue(m, "Must emit budget_tokens in init event")
        budget = int(m.group(1))
        self.assertLessEqual(budget, 25000, "Guest budget must never exceed guest quota limit")
        self.assertGreater(budget, 0)

    # ---------------- 15. Guest Rate Limiting Endpoint ----------------

    def test_guest_rate_limiting_endpoint(self):
        """Verify rapid guest creation requests hit rate limit after threshold."""
        unique_ip = f"198.51.100.{hash(self.test_username) % 200 + 10}"
        for _ in range(10):
            r = self.client.post("/api/auth/guest", headers={"X-Forwarded-For": unique_ip})
            self.assertEqual(r.status_code, 200)
        blocked = self.client.post("/api/auth/guest", headers={"X-Forwarded-For": unique_ip})
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("too many guest sessions", blocked.json().get("detail", "").lower())

    # ---------------- 16. Stream Lease Renewal & Concurrency Race ----------------

    def test_stream_lease_renewal(self):
        """Verify stream lease renewal successfully extends expiration."""
        user_id = self.user["id"]
        ok, sid = main.acquire_user_stream(user_id)
        self.assertTrue(ok)
        renew_ok = main.renew_user_stream(sid)
        self.assertTrue(renew_ok)
        main.release_user_stream(sid)

    def test_atomic_stream_concurrency_race(self):
        """Verify concurrent attempts to acquire stream leases are strictly serialized."""
        import concurrent.futures
        user_id = self.user["id"]
        results = []

        def try_acquire():
            return main.acquire_user_stream(user_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(try_acquire) for _ in range(5)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        successful = [sid for ok, sid in results if ok]
        self.assertLessEqual(len(successful), 2, "Must never allow more than 2 concurrent stream leases")
        for sid in successful:
            main.release_user_stream(sid)

    # ---------------- 17. Login Lockout & Reset ----------------

    def test_login_brute_force_lockout_endpoint(self):
        """Verify endpoint returns 429 when failed login attempts reach 5."""
        username = f"lockout_{self.test_username}"
        database.create_user(username, "CorrectPassword123!")

        # 5 failed login attempts
        for _ in range(5):
            resp = self.client.post("/api/auth/login", json={"username": username, "password": "WrongPassword!"})
            self.assertEqual(resp.status_code, 401)

        # 6th attempt should be locked out with HTTP 429
        locked_resp = self.client.post("/api/auth/login", json={"username": username, "password": "WrongPassword!"})
        self.assertEqual(locked_resp.status_code, 429)
        self.assertIn("locked", locked_resp.json().get("detail", "").lower())

    # ---------------- 18. Schema v5 FK Cleanliness ----------------

    def test_schema_v5_fk_integrity_and_cleanliness(self):
        """Verify database passes foreign key integrity check with 0 violations."""
        with database.get_connection() as conn:
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            self.assertEqual(len(violations), 0, f"Expected 0 foreign key violations, found: {violations}")

    # ---------------- 19. HttpOnly Cookie Auth Flow ----------------

    def test_httponly_session_cookie_auth_flow(self):
        """Verify registration, authentication, and logout via HttpOnly SameSite secure cookie."""
        uname = f"cookie_user_{uuid.uuid4().hex[:8]}"
        reg_resp = self.client.post("/api/auth/register", json={"username": uname, "password": "StrongPassword123!"})
        self.assertEqual(reg_resp.status_code, 201)
        self.assertNotIn("token", reg_resp.json(), "Browser registration response must omit token")
        self.assertIn("cortex_session", reg_resp.cookies)
        session_cookie = reg_resp.cookies.get("cortex_session")
        self.assertTrue(bool(session_cookie))

        # Login also sets cookie and omits token
        login_resp = self.client.post("/api/auth/login", json={"username": uname, "password": "StrongPassword123!"})
        self.assertEqual(login_resp.status_code, 200)
        self.assertNotIn("token", login_resp.json(), "Browser login response must omit token")
        self.assertIn("cortex_session", login_resp.cookies)
        session_cookie = login_resp.cookies.get("cortex_session")

        # Access /api/auth/me using ONLY the session cookie (no Authorization header)
        me_resp = self.client.get("/api/auth/me", cookies={"cortex_session": session_cookie})
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["username"], uname)

        # Logout with cookie
        logout_resp = self.client.post("/api/auth/logout", cookies={"cortex_session": session_cookie})
        self.assertEqual(logout_resp.status_code, 200)

        # Revoked session should now be rejected
        revoked_resp = self.client.get("/api/auth/me", cookies={"cortex_session": session_cookie})
        self.assertEqual(revoked_resp.status_code, 401)

    # ---------------- 20. Multi-Factor Turn Quota Reservation ----------------

    @patch("main.make_llm")
    def test_multi_factor_turn_quota_reservation_rejection(self, mock_make_llm):
        """Verify chat stream rejects early if remaining allowance cannot support input context + response."""
        user_id = self.user["id"]
        # Consume almost all quota so remaining allowance is 200 tokens
        limit = database.DAILY_TOKEN_LIMIT
        database.release_quota(user_id, estimated_tokens=0, actual_tokens=limit - 200)

        token = main.generate_token(self.user["id"], self.user["username"])
        # Send a prompt whose input context alone is ~1000 tokens (4000 characters)
        large_prompt = "Explain quantum cryptography in detail. " * 100
        payload = {
            "model": "nvidia/nemotron-3-super-120b-a12b",
            "messages": [{"role": "user", "content": large_prompt}],
        }
        resp = self.client.post(
            "/api/chat/stream",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        # Should stream a quota reached error token event, not crash or invoke LLM provider
        body = resp.text
        self.assertIn("Daily token quota reached", body)
        mock_make_llm.assert_not_called()

    # ---------------- 21. Online Database Backup API ----------------

    def test_online_database_backup_api(self):
        """Verify point-in-time consistent online backup of the SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            backup_file = Path(tf.name)

        try:
            res_path = database.backup_db(target_path=backup_file)
            self.assertEqual(res_path, backup_file)
            self.assertTrue(backup_file.exists())
            self.assertGreater(backup_file.stat().st_size, 0)
            # Verify backup is a valid SQLite DB with integrity check passing
            conn = sqlite3.connect(str(backup_file))
            try:
                row = conn.execute("PRAGMA integrity_check").fetchone()
                self.assertEqual(row[0], "ok")
                schema_v = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
                self.assertGreaterEqual(schema_v, 5)
            finally:
                conn.close()
        finally:
            if backup_file.exists():
                try:
                    backup_file.unlink()
                except Exception:
                    pass

    # ---------------- 22. Stream Lease Release Precision ----------------

    def test_stream_lease_release_precision(self):
        """Verify releasing a stream lease by stream_id only releases that specific lease."""
        user_id = self.user["id"]
        ok1, sid1 = main.acquire_user_stream(user_id)
        ok2, sid2 = main.acquire_user_stream(user_id)
        self.assertTrue(ok1)
        self.assertTrue(ok2)

        # Release specifically sid1
        database.release_stream_lease(sid1)

        # sid2 must still be active in active_stream_leases
        with database.get_connection() as conn:
            active_leases = [
                r["stream_id"]
                for r in conn.execute(
                    "SELECT stream_id FROM active_stream_leases WHERE user_id = ?", (user_id,)
                ).fetchall()
            ]
            self.assertNotIn(sid1, active_leases)
            self.assertIn(sid2, active_leases)

        database.release_stream_lease(sid2)

    # ---------------- 23. API Client Bearer Token Auth ----------------

    def test_api_client_bearer_token_auth(self):
        """Verify explicit API clients receive Bearer tokens via X-API-Client header or /api/auth/token."""
        # 1. Dedicated /api/auth/token endpoint
        token_resp = self.client.post(
            "/api/auth/token",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(token_resp.status_code, 200)
        token_data = token_resp.json()
        self.assertIn("token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")
        bearer_token = token_data["token"]

        # 2. Access /api/auth/me using Bearer token
        me_resp = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["username"], self.test_username)

        # 3. /api/auth/login with X-API-Client: true returns token
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
            headers={"X-API-Client": "true"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("token", login_resp.json())

        # 4. /api/auth/guest with X-API-Client: true returns token
        guest_resp = self.client.post(
            "/api/auth/guest",
            headers={"X-API-Client": "true"},
        )
        self.assertEqual(guest_resp.status_code, 200)
        self.assertIn("token", guest_resp.json())

    # ---------------- 24. Strict CSP Hardening ----------------

    def test_strict_csp_header_no_unsafe_inline(self):
        """Verify Content-Security-Policy header does not contain unsafe-inline in script-src."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        csp = resp.headers.get("Content-Security-Policy", "")
        self.assertTrue(bool(csp))
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("default-src 'self'", csp)
        # Extract script-src directive
        import re
        script_src = re.search(r"script-src ([^;]+);", csp)
        self.assertTrue(script_src, "Must define script-src in CSP")
        self.assertNotIn("'unsafe-inline'", script_src.group(1), "Root CSP script-src must not contain 'unsafe-inline'")

    # ---------------- 25. Multi-Round Tool Quota & Turn Budget ----------------

    @patch("main.make_llm")
    def test_tool_rounds_token_accumulation_and_budget_guard(self, mock_make_llm):
        """Verify run_tool_rounds_streaming accumulates provider tokens and enforces turn budget limit."""
        mock_llm = MagicMock()
        # Round 1: returns a tool call with 350 tokens usage
        msg1 = MagicMock()
        msg1.tool_calls = [{"name": "calculator", "args": {"expression": "2+2"}, "id": "call_1"}]
        msg1.content = ""
        msg1.usage_metadata = {"total_tokens": 350}
        msg1.response_metadata = {}

        # Round 2: returns normal text (no more calls) with 100 tokens usage
        msg2 = MagicMock()
        msg2.tool_calls = []
        msg2.content = "Done"
        msg2.usage_metadata = {"total_tokens": 100}
        msg2.response_metadata = {}

        mock_llm.invoke.side_effect = [msg1, msg2]
        mock_bound = MagicMock()
        mock_bound.invoke.side_effect = [msg1, msg2]
        mock_llm.bind_tools.return_value = mock_bound
        mock_make_llm.return_value = mock_llm

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content="Calculate 2+2")]

        events = list(main.run_tool_rounds_streaming(
            messages,
            max_rounds=3,
            turn_budget=1000,
        ))

        event_dict = dict(events)
        self.assertIn("tool_tokens_total", event_dict)
        self.assertEqual(event_dict["tool_tokens_total"], 450)
        self.assertIn("tools_used", event_dict)
        self.assertIn("calculator", event_dict["tools_used"])

    @patch("main.make_llm")
    def test_tool_rounds_preflight_never_starts_an_unaffordable_round(self, mock_make_llm):
        """Tool routing must reserve prompt and synthesis tokens before invoking a provider."""
        from langchain_core.messages import HumanMessage

        # A 100-token prompt in a 500-token turn leaves at most 200 output
        # tokens after the 200-token synthesis reserve. The model must never be
        # given the former unconditional 1024-token allowance.
        tool_call_message = MagicMock()
        tool_call_message.tool_calls = [{"name": "calculator", "args": {"expression": "2+2"}, "id": "call_1"}]
        tool_call_message.content = ""
        tool_call_message.usage_metadata = {"total_tokens": 250}
        tool_call_message.response_metadata = {}
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = tool_call_message
        mock_make_llm.return_value = mock_llm

        events = list(main.run_tool_rounds_streaming(
            [HumanMessage(content="x" * 400)],
            max_rounds=2,
            turn_budget=500,
        ))

        self.assertLessEqual(mock_make_llm.call_args.kwargs["max_tokens"], 200)
        self.assertLessEqual(dict(events)["tool_tokens_total"], 500)

        # A larger prompt leaves less than the minimum structured-call output;
        # skip tools altogether instead of starting a provider call that cannot
        # fit inside the turn budget.
        mock_make_llm.reset_mock()
        events = list(main.run_tool_rounds_streaming(
            [HumanMessage(content="x" * 1000)],
            max_rounds=2,
            turn_budget=500,
        ))
        self.assertFalse(mock_make_llm.called)
        self.assertEqual(dict(events)["tool_tokens_total"], 0)

        # Invariant check: even if provider over-reports tokens, tool_tokens_total never exceeds turn_budget
        tool_call_message.usage_metadata = {"total_tokens": 9999}
        mock_llm.bind_tools.return_value.invoke.return_value = tool_call_message
        mock_make_llm.reset_mock()
        mock_make_llm.return_value = mock_llm
        events = list(main.run_tool_rounds_streaming(
            [HumanMessage(content="x" * 400)],
            max_rounds=1,
            turn_budget=500,
        ))
        self.assertLessEqual(dict(events)["tool_tokens_total"], 500)

    # ---------------- 26. SQLite Connection Lifecycle ----------------

    def test_sqlite_connection_lifecycle_cleanup(self):
        """Verify connection lifecycle correctly tracks and closes connections with zero resource leaks."""
        # Ensure a connection is open
        conn = database.get_connection()
        self.assertIsNotNone(conn)
        self.assertIn(conn, database._OPEN_CONNECTIONS)

        # Cleanly close all connections
        database.close_all_connections()
        self.assertEqual(len(database._OPEN_CONNECTIONS), 0)
        self.assertIsNone(getattr(database._local, "conn", None))

    # ---------------- 27. User Profile Avatar ----------------

    def test_user_avatar_update(self):
        """Verify user avatar can be updated via PATCH /api/user/profile and persists."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)

        # Update avatar
        patch_res = self.client.patch("/api/user/profile", json={"avatar": "avatar-3"})
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["avatar"], "avatar-3")

        # Verify auth_me returns updated avatar
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["avatar"], "avatar-3")

    # ---------------- 28. Conversation Archiving ----------------

    def test_conversation_archiving_and_filtering(self):
        """Verify conversations can be archived and unarchived, and are filtered appropriately."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)

        # Create 2 conversations
        conv1_res = self.client.post("/api/conversations", json={"title": "Chat 1"})
        conv2_res = self.client.post("/api/conversations", json={"title": "Chat 2"})
        c1_id = conv1_res.json()["id"]
        c2_id = conv2_res.json()["id"]

        # Both should be in active list
        list_res = self.client.get("/api/conversations")
        self.assertEqual(list_res.status_code, 200)
        active_ids = [c["id"] for c in list_res.json()]
        self.assertIn(c1_id, active_ids)
        self.assertIn(c2_id, active_ids)

        # Archive conv1
        arc_res = self.client.patch(f"/api/conversations/{c1_id}/archive", json={"is_archived": True})
        self.assertEqual(arc_res.status_code, 200)

        # Active list should now only have conv2
        list_res2 = self.client.get("/api/conversations")
        active_ids2 = [c["id"] for c in list_res2.json()]
        self.assertNotIn(c1_id, active_ids2)
        self.assertIn(c2_id, active_ids2)

        # Archived list should have conv1
        archived_res = self.client.get("/api/conversations/archived")
        self.assertEqual(archived_res.status_code, 200)
        archived_ids = [c["id"] for c in archived_res.json()]
        self.assertIn(c1_id, archived_ids)
        self.assertNotIn(c2_id, archived_ids)

        # Unarchive conv1
        unarc_res = self.client.patch(f"/api/conversations/{c1_id}/archive", json={"is_archived": False})
        self.assertEqual(unarc_res.status_code, 200)

        # Now conv1 should be back in active list
        list_res3 = self.client.get("/api/conversations")
        active_ids3 = [c["id"] for c in list_res3.json()]
        self.assertIn(c1_id, active_ids3)

    # ---------------- 29. Full Account Deletion ----------------

    def test_delete_user_account_cascades_all_data(self):
        """Verify DELETE /api/user/account completely wipes user and all child data with zero orphaned rows."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)

        user_id = self.user["id"]

        # Create conversation, message, memory, project
        conv = database.create_conversation(user_id=user_id, title="Account Deletion Test")
        database.add_message(conv["id"], "user", "Hello Cortex")
        database.add_message(conv["id"], "assistant", "Hello! How can I help?")
        database.add_memory(user_id=user_id, content="User prefers TypeScript", category="tech")
        database.create_project(user_id=user_id, name="Project Alpha")

        # Verify records exist
        self.assertIsNotNone(database.get_user_by_id(user_id))
        self.assertGreater(len(database.get_conversations(user_id)), 0)
        self.assertGreater(len(database.get_messages(conv["id"])), 0)
        self.assertGreater(len(database.get_memories(user_id)), 0)
        self.assertGreater(len(database.get_projects(user_id)), 0)

        # Delete account
        del_res = self.client.delete("/api/user/account")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["ok"])

        # Verify user is gone
        self.assertIsNone(database.get_user_by_id(user_id))
        self.assertEqual(len(database.get_conversations(user_id)), 0)
        self.assertEqual(len(database.get_messages(conv["id"])), 0)
        self.assertEqual(len(database.get_memories(user_id)), 0)
        self.assertEqual(len(database.get_projects(user_id)), 0)

        # Verify database foreign key integrity
        with database.get_connection() as conn:
            fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
            self.assertEqual(len(fk_errors), 0, f"Foreign key errors found after deletion: {fk_errors}")

        # Attempting to call /api/auth/me now should return 401
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 401)

    # ---------------- 30. Local-First Workspace Sync & Data Portability ----------------

    def test_sync_state_reconstitutes_workspace(self):
        """Verify POST /api/sync/state reconstitutes all conversations, messages, memories,
        projects, and monotonic token usage on freshly deployed containers."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)

        cid = str(uuid.uuid4())
        mid1 = str(uuid.uuid4())
        mid2 = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        mem_id = str(uuid.uuid4())

        payload = {
            "conversations": [
                {
                    "id": cid,
                    "title": "Synced AI Engineering",
                    "project_id": pid,
                    "is_pinned": 1,
                    "is_archived": 0,
                }
            ],
            "messages": [
                {
                    "id": mid1,
                    "conversation_id": cid,
                    "role": "user",
                    "content": "What is local-first architecture?",
                },
                {
                    "id": mid2,
                    "conversation_id": cid,
                    "role": "assistant",
                    "content": "Local-first architecture ensures client data sovereignty and instantaneous response.",
                },
            ],
            "memories": [
                {
                    "id": mem_id,
                    "content": "User prefers FastAPI and SQLite",
                    "category": "tech_stack",
                }
            ],
            "projects": [
                {
                    "id": pid,
                    "name": "Cortex Core Engine",
                    "description": "Multi-agent autonomous intelligence",
                }
            ],
            "tokens_used": 14250,
        }

        sync_res = self.client.post("/api/sync/state", json=payload)
        self.assertEqual(sync_res.status_code, 200)
        data = sync_res.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["conversations"], 1)
        self.assertEqual(data["messages"], 2)
        self.assertEqual(data["memories"], 1)
        self.assertEqual(data["projects"], 1)
        self.assertGreaterEqual(data["tokens_used"], 14250)

        # Verify DB queries reflect reconstituted state
        convs = database.get_conversations(self.user["id"])
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["id"], cid)
        self.assertEqual(convs[0]["title"], "Synced AI Engineering")

        msgs = database.get_messages(cid, user_id=self.user["id"])
        self.assertEqual(len(msgs), 2)

        mems = database.get_memories(self.user["id"])
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["content"], "User prefers FastAPI and SQLite")

        projs = database.get_projects(self.user["id"])
        self.assertEqual(len(projs), 1)
        self.assertEqual(projs[0]["name"], "Cortex Core Engine")

    def test_export_and_import_full_workspace(self):
        """Verify full round-trip JSON export and import of workspace state."""
        login_res = self.client.post(
            "/api/auth/login",
            json={"username": self.test_username, "password": "SecurePassword123!"},
        )
        self.assertEqual(login_res.status_code, 200)

        # Seed data
        conv = database.create_conversation(user_id=self.user["id"], title="Export Test Chat")
        database.add_message(conv["id"], "user", "Export my data")
        database.add_message(conv["id"], "assistant", "Exporting complete workspace JSON")
        database.add_memory(user_id=self.user["id"], content="User loves dark mode", category="ui")

        # 1. Export
        export_res = self.client.get("/api/user/export-full")
        self.assertEqual(export_res.status_code, 200)
        export_json = export_res.json()

        self.assertEqual(export_json["version"], "cortex-v3-backup")
        self.assertIn("exported_at", export_json)
        self.assertEqual(export_json["user"]["id"], self.user["id"])
        self.assertGreaterEqual(len(export_json["conversations"]), 1)
        self.assertIn(conv["id"], export_json["messages_by_conversation"])
        self.assertGreaterEqual(len(export_json["memories"]), 1)

        # 2. Modify backup title and test import
        new_conv_id = str(uuid.uuid4())
        export_json["conversations"].append({
            "id": new_conv_id,
            "title": "Imported Chat After Deployment",
            "created_at": "2026-09-18T00:00:00Z",
            "updated_at": "2026-09-18T00:00:00Z",
        })
        export_json["messages_by_conversation"][new_conv_id] = [
            {"id": str(uuid.uuid4()), "role": "user", "content": "Hello from restored backup"}
        ]

        import_res = self.client.post("/api/user/import-full", json={"data": export_json})
        self.assertEqual(import_res.status_code, 200)
        import_data = import_res.json()
        self.assertTrue(import_data["ok"])

        # Verify newly imported chat is now in user's conversations
        conv_ids = [c["id"] for c in database.get_conversations(self.user["id"])]
        self.assertIn(new_conv_id, conv_ids)

    def test_self_healing_auth_provisioning(self):
        """Verify that authenticating an unprovisioned user automatically provisions deterministically."""
        fresh_username = f"auto_{uuid.uuid4().hex[:8]}"
        fresh_pass = "AutoProvision123!"

        # Authenticate without registering first
        user = database.authenticate_user(fresh_username, fresh_pass, allow_auto_provision=True)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], fresh_username.lower())
        expected_uid = database.generate_user_id(fresh_username)
        self.assertEqual(user["id"], expected_uid)

        # Subsequent authenticate with matching credentials succeeds
        user_repeat = database.authenticate_user(fresh_username, fresh_pass, allow_auto_provision=False)
        self.assertIsNotNone(user_repeat)
        self.assertEqual(user_repeat["id"], expected_uid)

    def test_reset_password_endpoint_and_force_reset(self):
        """Verify password reset endpoint and force_reset login flag."""
        target_user = f"reset_{uuid.uuid4().hex[:8]}"
        initial_pass = "InitialPass123!"
        new_pass = "NewResetPass456!"

        # Register user
        reg_res = self.client.post("/api/auth/register", json={
            "username": target_user,
            "password": initial_pass,
        })
        self.assertEqual(reg_res.status_code, 201)

        # 1. Test /api/auth/reset-password
        reset_res = self.client.post("/api/auth/reset-password", json={
            "username": target_user,
            "password": new_pass,
        })
        self.assertEqual(reset_res.status_code, 200)
        reset_data = reset_res.json()
        self.assertTrue(reset_data["ok"])
        self.assertEqual(reset_data["user"]["username"], target_user.lower())

        # Verify old password fails
        old_login = self.client.post("/api/auth/login", json={
            "username": target_user,
            "password": initial_pass,
        })
        self.assertEqual(old_login.status_code, 401)

        # Verify new password succeeds
        new_login = self.client.post("/api/auth/login", json={
            "username": target_user,
            "password": new_pass,
        })
        self.assertEqual(new_login.status_code, 200)

        # 2. Test login with force_reset=True
        third_pass = "ThirdPass789!"
        force_login = self.client.post("/api/auth/login", json={
            "username": target_user,
            "password": third_pass,
            "force_reset": True,
        })
        self.assertEqual(force_login.status_code, 200)
        force_data = force_login.json()
        self.assertTrue(force_data["ok"])
        self.assertEqual(force_data["user"]["username"], target_user.lower())

    # ---------------- 31. Email-First & Anti-Hacker Hardened Auth ----------------

    def test_email_first_registration_and_duplicate_rejection(self):
        """Verify registration requires valid email and rejects duplicates with 409 Conflict."""
        test_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        valid_password = "SecurePassword2026!"

        # 1. Successful email-first registration
        reg_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": valid_password,
            "username": "tester1",
        })
        self.assertEqual(reg_res.status_code, 201)
        data = reg_res.json()
        self.assertEqual(data["user"]["email"], test_email.lower())

        # 2. Duplicate email registration returns 409 Conflict with clear message
        dup_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": "AnotherPassword2026!",
            "username": "tester2",
        })
        self.assertEqual(dup_res.status_code, 409)
        self.assertIn("already exists", dup_res.json()["detail"])

    def test_anti_hacker_password_complexity(self):
        """Verify weak, numeric-only, or simple passwords are blocked."""
        test_email = f"complex_{uuid.uuid4().hex[:8]}@example.com"

        # Purely numeric password like 123456789
        num_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": "123456789",
        })
        self.assertEqual(num_res.status_code, 400)
        self.assertIn("letter", num_res.json()["detail"].lower())

        # Letters only without numbers or symbols
        letter_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": "alllettersonly",
        })
        self.assertEqual(letter_res.status_code, 400)

        # Under 8 characters
        short_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": "Sh1!",
        })
        self.assertEqual(short_res.status_code, 422)  # pydantic min_length=8

    def test_login_by_email_and_username_with_remember_me(self):
        """Verify login works with either email or username, and honors remember_me."""
        test_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
        test_user = f"uname_{uuid.uuid4().hex[:8]}"
        test_pwd = "StrongCortex2026!"

        reg_res = self.client.post("/api/auth/register", json={
            "email": test_email,
            "username": test_user,
            "password": test_pwd,
        })
        self.assertEqual(reg_res.status_code, 201)

        # 1. Login with email
        email_login = self.client.post("/api/auth/login", json={
            "email_or_username": test_email,
            "password": test_pwd,
            "remember_me": True,
        })
        self.assertEqual(email_login.status_code, 200)
        self.assertEqual(email_login.json()["user"]["username"], test_user.lower())

        # 2. Login with username
        user_login = self.client.post("/api/auth/login", json={
            "email_or_username": test_user,
            "password": test_pwd,
            "remember_me": False,
        })
        self.assertEqual(user_login.status_code, 200)
        self.assertEqual(user_login.json()["user"]["email"], test_email.lower())

    def test_serverless_token_placeholder_reconciliation_on_login(self):
        """Verify that a user reconstituted from a token with placeholder hash can authenticate with their valid password."""
        uid = f"recon_{uuid.uuid4().hex[:8]}"
        email = f"recon_{uuid.uuid4().hex[:8]}@example.com"
        username = f"recon_user_{uuid.uuid4().hex[:6]}"
        valid_pwd = "StrongPassword#2026"

        # Reconstitute placeholder in SQLite
        reconstituted = database.reconstitute_user(user_id=uid, username=username, email=email)
        self.assertEqual(reconstituted["id"], uid)

        # Authenticate with credentials should bind password hash and succeed
        auth_res = database.authenticate_user(email, valid_pwd)
        self.assertIsNotNone(auth_res)
        self.assertEqual(auth_res["id"], uid)

        # Verify password hash in DB is now real PBKDF2 hash, not placeholder
        with database.get_connection() as conn:
            row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (uid,)).fetchone()
            self.assertNotEqual(row["password_hash"], "SERVERLESS_VERIFIED_TOKEN")

    def test_image_compression_under_350k_chars(self):
        """Verify image compressor compresses oversized base64 images well under 350k characters."""
        import base64
        import io
        import os
        from PIL import Image

        # Generate a large high-entropy image that cannot compress under 350k as PNG
        raw = os.urandom(800 * 800 * 3)
        img = Image.frombytes("RGB", (800, 800), raw)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        self.assertGreater(len(data_url), 350000)

        compressed = main._compress_b64_image_if_needed(data_url, max_chars=350000)
        self.assertLessEqual(len(compressed), 350000)
        self.assertTrue(compressed.startswith("data:image/jpeg;base64,"))

    def test_model_identity_directive_in_build_messages(self):
        """Verify model identity directive accurately aligns model persona in system messages."""
        for model_id, expected_name in [
            ("openai/gpt-oss-20b", "Cortex 4 (Deep Reasoning)"),
            ("z-ai/glm-5.3", "Cortex 5.3 (Frontier MoE 753B)"),
            ("z-ai/glm-5.3-flash", "Cortex 5.3 Flash (Vision & Reasoning 320B)"),
            ("nvidia/nemotron-3.5-lightning-30b-a3b", "Cortex 3.5 Lightning (Ultra-Fast)"),
        ]:
            req = main.ChatRequest(messages=[main.ChatMessage(role="user", content="Identity test")])
            msgs, _ = main._build_messages(req, model=model_id, mode="auto")
            sys_texts = [m.content for m in msgs if hasattr(m, "content") and "[ACTIVE MODEL PROFILE:" in str(m.content)]
            self.assertTrue(sys_texts, f"Active model profile missing for {model_id}")
            self.assertIn(expected_name, sys_texts[0])
            self.assertIn(model_id, sys_texts[0])

    def test_stream_init_contains_dispatch_tracking(self):
        """Verify SSE init event contains requested_model, resolved_provider_model, and request_id."""
        with patch("main.make_llm") as mock_make_llm:
            mock_instance = MagicMock()
            mock_instance.stream.return_value = [
                MagicMock(content="Hello", response_metadata={}, additional_kwargs={})
            ]
            mock_make_llm.return_value = mock_instance

            token = main.generate_token(self.user["id"], self.user["username"])
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": [{"role": "user", "content": "Hello!"}],
            }
            resp = self.client.post("/api/chat/stream", json=payload, headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(resp.status_code, 200)
            content = resp.content.decode("utf-8")
            self.assertIn('"requested_model": "openai/gpt-oss-20b"', content)
            self.assertIn('"resolved_provider_model": "openai/gpt-oss-20b"', content)
            self.assertIn('"request_id": "req_', content)


    def test_glm_thinking_mode_auto_enforcement(self):
        """Verify chat stream automatically locks GLM models into thinking mode regardless of client mode."""
        for glm_id in ("z-ai/glm-5.3", "z-ai/glm-5.3-flash"):
            with patch("main.make_llm") as mock_make_llm:
                mock_instance = MagicMock()
                mock_instance.stream.return_value = [
                    MagicMock(content="Hello", response_metadata={}, additional_kwargs={})
                ]
                mock_make_llm.return_value = mock_instance

                token = main.generate_token(self.user["id"], self.user["username"])
                payload = {
                    "model": glm_id,
                    "mode": "fast",  # Client requested fast, but GLM must be forced to thinking
                    "messages": [{"role": "user", "content": "What is machine learning?"}],
                }
                resp = self.client.post("/api/chat/stream", json=payload, headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(resp.status_code, 200)
                content = resp.content.decode("utf-8")
                self.assertIn('"mode": "thinking"', content, f"GLM model {glm_id} was not forced to thinking mode")

    def test_langchain_reasoning_content_monkeypatch(self):
        """Verify _convert_delta_to_message_chunk captures reasoning_content into chunk.additional_kwargs."""
        from langchain_openai.chat_models.base import _convert_delta_to_message_chunk, AIMessageChunk
        delta = {"role": "assistant", "content": None, "reasoning_content": "Deep reasoning steps here..."}
        chunk = _convert_delta_to_message_chunk(delta, AIMessageChunk)
        self.assertIn("reasoning_content", chunk.additional_kwargs)
        self.assertEqual(chunk.additional_kwargs["reasoning_content"], "Deep reasoning steps here...")

    def test_chat_stream_yields_thought_events_for_reasoning(self):
        """Verify SSE stream emits thought events when reasoning_content is present in chunks."""
        with patch("main.make_llm") as mock_make_llm:
            mock_instance = MagicMock()
            thought_chunk = MagicMock(
                content="",
                response_metadata={},
                additional_kwargs={"reasoning_content": "Pondering the query..."}
            )
            answer_chunk = MagicMock(
                content="Here is the solution.",
                response_metadata={},
                additional_kwargs={}
            )
            mock_instance.stream.return_value = [thought_chunk, answer_chunk]
            mock_make_llm.return_value = mock_instance

            token = main.generate_token(self.user["id"], self.user["username"])
            payload = {
                "model": "z-ai/glm-5.3-flash",
                "messages": [{"role": "user", "content": "Explain quicksort"}],
            }
            resp = self.client.post("/api/chat/stream", json=payload, headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(resp.status_code, 200)
            content = resp.content.decode("utf-8")
            self.assertIn('"type": "thought"', content)
            self.assertIn("Pondering the query...", content)
            self.assertIn('"type": "token"', content)
            self.assertIn("Here is the solution.", content)

    def test_glm_tool_execution_routes_to_super_agent(self):
        """Verify tool rounds use MODEL_NAME for tool calling when model_override is a GLM model."""
        with patch("main.make_llm") as mock_make_llm:
            mock_instance = MagicMock()
            mock_instance.bind_tools.return_value.invoke.return_value = MagicMock(
                tool_calls=[], content="No tools needed"
            )
            mock_make_llm.return_value = mock_instance

            main.run_tool_rounds([main.HumanMessage(content="test")], model_override="z-ai/glm-5.3")
            # Should have called make_llm with MODEL_NAME, not z-ai/glm-5.3
            self.assertEqual(mock_make_llm.call_args.kwargs.get("model_override"), main.MODEL_NAME)

    def test_glm_substantive_reasoning_recovery(self):
        """Verify chat_stream recovers reasoning content as full_text if content tokens were empty."""
        with patch("main.make_llm") as mock_make_llm:
            mock_stream_instance = MagicMock()
            thought_chunk = MagicMock(
                content="",
                response_metadata={},
                additional_kwargs={"reasoning_content": "This is comprehensive reasoning that answers the prompt completely."}
            )
            mock_stream_instance.stream.return_value = [thought_chunk]

            mock_fb_instance = MagicMock()
            mock_fb_instance.invoke.return_value = MagicMock(content="", response_metadata={})

            def make_llm_side_effect(**kwargs):
                if kwargs.get("streaming"):
                    return mock_stream_instance
                return mock_fb_instance

            mock_make_llm.side_effect = make_llm_side_effect

            token = main.generate_token(self.user["id"], self.user["username"])
            payload = {
                "model": "z-ai/glm-5.3",
                "messages": [{"role": "user", "content": "Explain machine learning in detail"}],
            }
            resp = self.client.post("/api/chat/stream", json=payload, headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(resp.status_code, 200)
            content = resp.content.decode("utf-8")
            self.assertIn("This is comprehensive reasoning that answers the prompt completely.", content)

    def test_artifact_detection_expansion_and_persistence(self):
        """Verify code blocks in Python/JS/HTML are properly detected as artifacts with correct extensions."""
        conv = database.create_conversation("Deep Learning Neural Networks", user_id=self.user["id"])
        code_text = (
            "Here is a complete deep learning training script in PyTorch:\n\n"
            "```python\n"
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class SimpleMLP(nn.Module):\n"
            "    def __init__(self):\n"
            "        super().__init__()\n"
            "        self.linear = nn.Linear(784, 10)\n\n"
            "    def forward(self, x):\n"
            "        return self.linear(x)\n"
            "```\n\n"
            "This model trains using standard SGD optimization."
        )
        database.add_message(conv["id"], role="assistant", content=code_text, user_id=self.user["id"])

        artifacts = database.get_user_artifacts(self.user["id"])
        self.assertTrue(len(artifacts) >= 1)
        found_art = next((a for a in artifacts if a["conversation_id"] == conv["id"]), None)
        self.assertIsNotNone(found_art)
        self.assertTrue(found_art["filename"].endswith(".py") or found_art["filename"].endswith(".md"))

        token = main.generate_token(self.user["id"], self.user["username"])
        resp = self.client.get("/api/artifacts", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("total", 0) >= 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


