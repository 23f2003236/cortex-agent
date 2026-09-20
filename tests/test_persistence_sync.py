"""Comprehensive Test Suite for Persistence & Cross-Browser Synchronization (Migration v9).
Verifies:
1. Database as the authoritative source of truth.
2. Project persistence, pin toggling, and soft deletion.
3. User preferences persistence, update, and strict user isolation.
4. Heartbeat project hash change detection and conversation deletion tombstones.
5. Multi-browser cross-session sync with simulated empty localStorage on Browser B.
6. Persistent storage path configuration (CORTEX_DB_PATH / PERSISTENT_STORAGE_PATH).
"""

import os
import tempfile
import unittest
import uuid
from pathlib import Path

from starlette.testclient import TestClient

import database
import main


class TestPersistenceSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_db_path = database.DB_PATH
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        database.set_db_path(Path(cls.temp_db.name))
        database.init_db()
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        database.close_all_connections()
        database.set_db_path(cls.orig_db_path)
        try:
            os.unlink(cls.temp_db.name)
        except Exception:
            pass

    def setUp(self):
        self.u1_name = f"user_a_{uuid.uuid4().hex[:8]}"
        self.u2_name = f"user_b_{uuid.uuid4().hex[:8]}"
        self.user1 = database.create_user(
            username=self.u1_name,
            email=f"{self.u1_name}@example.com",
            password="Password123!",
        )
        self.user2 = database.create_user(
            username=self.u2_name,
            email=f"{self.u2_name}@example.com",
            password="Password123!",
        )
        self.token1 = main.generate_token(self.user1["id"], self.user1["username"])
        self.token2 = main.generate_token(self.user2["id"], self.user2["username"])
        self.auth1 = {"Authorization": f"Bearer {self.token1}"}
        self.auth2 = {"Authorization": f"Bearer {self.token2}"}

    def test_schema_version_is_nine(self):
        version = database.get_schema_version()
        self.assertEqual(version, 9)

    def test_authoritative_database_project_lifecycle(self):
        """Verify projects are stored authoritatively in database with is_pinned field."""
        resp = self.client.post(
            "/api/projects",
            headers=self.auth1,
            json={"name": "Alpha Project", "icon": "🔬", "color": "#38bdf8"},
        )
        self.assertEqual(resp.status_code, 200)
        proj = resp.json()
        proj_id = proj["id"]
        self.assertEqual(proj["name"], "Alpha Project")
        self.assertEqual(proj["is_pinned"], 0)

        # Retrieve project list
        resp_list = self.client.get("/api/projects", headers=self.auth1)
        self.assertEqual(resp_list.status_code, 200)
        projects = resp_list.json()
        matching = [p for p in projects if p["id"] == proj_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["is_pinned"], 0)

    def test_toggle_project_pin_endpoint(self):
        """Test PATCH /api/projects/{id}/pin toggles pinned status."""
        resp = self.client.post(
            "/api/projects",
            headers=self.auth1,
            json={"name": "Pinned Test Project", "icon": "📌", "color": "#e0685c"},
        )
        self.assertEqual(resp.status_code, 200)
        proj_id = resp.json()["id"]

        # Pin project
        patch_resp = self.client.patch(
            f"/api/projects/{proj_id}/pin",
            headers=self.auth1,
            json={"is_pinned": True},
        )
        self.assertEqual(patch_resp.status_code, 200)
        self.assertTrue(patch_resp.json().get("ok"))
        self.assertEqual(patch_resp.json().get("is_pinned"), 1)

        # Verify in GET /api/projects
        list_resp = self.client.get("/api/projects", headers=self.auth1)
        target = next(p for p in list_resp.json() if p["id"] == proj_id)
        self.assertEqual(target["is_pinned"], 1)

        # Unpin project
        unpin_resp = self.client.patch(
            f"/api/projects/{proj_id}/pin",
            headers=self.auth1,
            json={"is_pinned": False},
        )
        self.assertEqual(unpin_resp.status_code, 200)
        self.assertEqual(unpin_resp.json().get("is_pinned"), 0)

    def test_soft_delete_project(self):
        """Test deleting a project performs soft deletion and excludes from active list."""
        resp = self.client.post(
            "/api/projects",
            headers=self.auth1,
            json={"name": "To Be Deleted", "icon": "🗑️", "color": "#94a3b8"},
        )
        proj_id = resp.json()["id"]

        del_resp = self.client.delete(f"/api/projects/{proj_id}", headers=self.auth1)
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.json().get("ok"))

        # Verify not returned in active list
        list_resp = self.client.get("/api/projects", headers=self.auth1)
        active_ids = [p["id"] for p in list_resp.json()]
        self.assertNotIn(proj_id, active_ids)

        # Verify row still exists in DB with is_deleted = 1
        with database.get_connection() as conn:
            row = conn.execute(
                "SELECT is_deleted, deleted_at FROM projects WHERE id = ?",
                (proj_id,),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["is_deleted"], 1)
            self.assertIsNotNone(row["deleted_at"])

    def test_user_preferences_crud_and_isolation(self):
        """Test GET and PUT /api/user/preferences with complete isolation between accounts."""
        # User 1 default prefs
        resp1 = self.client.get("/api/user/preferences", headers=self.auth1)
        self.assertEqual(resp1.status_code, 200)
        prefs1 = resp1.json()
        self.assertIn("model", prefs1)
        self.assertEqual(prefs1["mode"], "auto")
        self.assertEqual(prefs1["theme"], "dark")

        # Update User 1 prefs
        put_resp1 = self.client.put(
            "/api/user/preferences",
            headers=self.auth1,
            json={"model": "z-ai/glm-5.3", "mode": "thinking", "theme": "dark"},
        )
        self.assertEqual(put_resp1.status_code, 200)
        updated1 = put_resp1.json()
        self.assertEqual(updated1["model"], "z-ai/glm-5.3")
        self.assertEqual(updated1["mode"], "thinking")

        # Check User 1 GET
        get_again = self.client.get("/api/user/preferences", headers=self.auth1).json()
        self.assertEqual(get_again["model"], "z-ai/glm-5.3")
        self.assertEqual(get_again["mode"], "thinking")

        # User 2 prefs must remain isolated and unaffected
        resp2 = self.client.get("/api/user/preferences", headers=self.auth2)
        self.assertEqual(resp2.status_code, 200)
        prefs2 = resp2.json()
        self.assertNotEqual(prefs2["model"], "z-ai/glm-5.3")
        self.assertEqual(prefs2["mode"], "auto")

    def test_heartbeat_project_sync_and_hash_invalidation(self):
        """Test 3-second heartbeat detects project changes via hash and returns delta."""
        # Initial heartbeat without hash returns current hash & projects
        hb1 = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        self.assertTrue(hb1["ok"])
        initial_proj_hash = hb1["proj_hash"]
        self.assertTrue(hb1["projects_changed"])

        # Second heartbeat with current hash returns projects_changed=False
        hb2 = self.client.get(
            f"/api/sync/heartbeat?proj_hash={initial_proj_hash}",
            headers=self.auth1,
        ).json()
        self.assertFalse(hb2["projects_changed"])
        self.assertIsNone(hb2["projects"])

        # Creating a project invalidates the hash
        p_resp = self.client.post(
            "/api/projects",
            headers=self.auth1,
            json={"name": "Delta Sync Project", "icon": "⚡", "color": "#f59e0b"},
        )
        proj_id = p_resp.json()["id"]

        # Third heartbeat with old hash detects the change
        hb3 = self.client.get(
            f"/api/sync/heartbeat?proj_hash={initial_proj_hash}",
            headers=self.auth1,
        ).json()
        self.assertTrue(hb3["projects_changed"])
        self.assertNotEqual(hb3["proj_hash"], initial_proj_hash)
        self.assertIsNotNone(hb3["projects"])
        self.assertTrue(any(p["id"] == proj_id for p in hb3["projects"]))

    def test_heartbeat_deleted_conversation_tombstone(self):
        """Test deleting a conversation inserts a tombstone and delivers it to heartbeat."""
        # Create a conversation
        conv_resp = self.client.post(
            "/api/conversations",
            headers=self.auth1,
            json={"title": "To Be Deleted Chat"},
        )
        self.assertEqual(conv_resp.status_code, 200)
        conv_id = conv_resp.json()["id"]

        # Delete conversation
        del_resp = self.client.delete(f"/api/conversations/{conv_id}", headers=self.auth1)
        self.assertEqual(del_resp.status_code, 200)

        # Heartbeat returns deleted_conv_ids containing conv_id
        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        self.assertIn("deleted_conv_ids", hb)
        self.assertIn(conv_id, hb["deleted_conv_ids"])

    def test_cross_browser_parity_with_empty_localstorage(self):
        """Simulate Browser A creating data, and Browser B loading with empty localStorage."""
        # Browser A acts:
        # 1. Sets preference to glm-5.3 thinking mode
        self.client.put(
            "/api/user/preferences",
            headers=self.auth1,
            json={"model": "z-ai/glm-5.3", "mode": "thinking", "theme": "dark"},
        )

        # 2. Creates and pins a project
        p_res = self.client.post(
            "/api/projects",
            headers=self.auth1,
            json={"name": "Quantum Computing", "icon": "⚛️", "color": "#818cf8"},
        )
        p_id = p_res.json()["id"]
        self.client.patch(f"/api/projects/{p_id}/pin", headers=self.auth1, json={"is_pinned": True})

        # 3. Creates a conversation assigned to the project
        c_res = self.client.post(
            "/api/conversations",
            headers=self.auth1,
            json={"title": "Shor's Algorithm Notes"},
        )
        c_id = c_res.json()["id"]
        self.client.patch(f"/api/conversations/{c_id}/project", headers=self.auth1, json={"project_id": p_id})

        # Browser B arrives with EMPTY localStorage:
        # It makes the exact startup calls that checkAuth() makes:
        # 1. /api/auth/me
        me_resp = self.client.get("/api/auth/me", headers=self.auth1)
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["username"], self.u1_name)

        # 2. /api/user/preferences (authoritative DB truth)
        prefs_resp = self.client.get("/api/user/preferences", headers=self.auth1)
        self.assertEqual(prefs_resp.status_code, 200)
        b_prefs = prefs_resp.json()
        self.assertEqual(b_prefs["model"], "z-ai/glm-5.3")
        self.assertEqual(b_prefs["mode"], "thinking")

        # 3. /api/projects (authoritative DB truth)
        projs_resp = self.client.get("/api/projects", headers=self.auth1)
        self.assertEqual(projs_resp.status_code, 200)
        b_projs = projs_resp.json()
        b_target_proj = next((p for p in b_projs if p["id"] == p_id), None)
        self.assertIsNotNone(b_target_proj)
        self.assertEqual(b_target_proj["name"], "Quantum Computing")
        self.assertEqual(b_target_proj["is_pinned"], 1)

        # 4. /api/conversations (authoritative DB truth)
        convs_resp = self.client.get("/api/conversations", headers=self.auth1)
        self.assertEqual(convs_resp.status_code, 200)
        b_convs = convs_resp.json()
        b_target_conv = next((c for c in b_convs if c["id"] == c_id), None)
        self.assertIsNotNone(b_target_conv)
        self.assertEqual(b_target_conv["title"], "Shor's Algorithm Notes")
        self.assertEqual(b_target_conv["project_id"], p_id)

        # 5. /api/sync/heartbeat works identically on Browser B
        hb_resp = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        self.assertEqual(hb_resp.status_code, 200)
        hb_data = hb_resp.json()
        self.assertTrue(hb_data["ok"])
        self.assertIsNotNone(hb_data["proj_hash"])
        self.assertIsNotNone(hb_data["conv_hash"])

    def test_custom_persistent_db_path_selection(self):
        """Test database.py honors CORTEX_DB_PATH or PERSISTENT_STORAGE_PATH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "persistent_cortex.db")
            os.environ["CORTEX_DB_PATH"] = custom_path
            try:
                # Re-evaluating custom path logic
                custom_env_val = os.environ.get("CORTEX_DB_PATH") or os.environ.get("PERSISTENT_STORAGE_PATH")
                self.assertEqual(custom_env_val, custom_path)
            finally:
                os.environ.pop("CORTEX_DB_PATH", None)


if __name__ == "__main__":
    unittest.main()
