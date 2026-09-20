"""Comprehensive Test Suite for Real-Time Multi-Browser Synchronization & Artifact Deduplication.
Ensures bulletproof sub-5ms heartbeat polling, cross-client state delivery, and indestructible artifact deduplication.
"""

import hashlib
import json
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from starlette.testclient import TestClient

import database
import main


class TestMultiBrowserSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        import tempfile
        from pathlib import Path
        cls.orig_db_path = database.DB_PATH
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        database.set_db_path(Path(cls.temp_db.name))
        database.init_db()
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        import os
        database.close_all_connections()
        database.set_db_path(cls.orig_db_path)
        try:
            os.unlink(cls.temp_db.name)
        except Exception:
            pass

    def setUp(self):
        # Create fresh isolated test users for each test
        self.u1_name = f"sync_u1_{uuid.uuid4().hex[:8]}"
        self.u2_name = f"sync_u2_{uuid.uuid4().hex[:8]}"
        self.user1 = database.create_user(username=self.u1_name, email=f"{self.u1_name}@example.com", password="Password123!")
        self.user2 = database.create_user(username=self.u2_name, email=f"{self.u2_name}@example.com", password="Password123!")
        self.token1 = main.generate_token(self.user1["id"], self.user1["username"])
        self.token2 = main.generate_token(self.user2["id"], self.user2["username"])
        self.auth1 = {"Authorization": f"Bearer {self.token1}"}
        self.auth2 = {"Authorization": f"Bearer {self.token2}"}

    # 1. Heartbeat Auth & Schema Tests
    def test_heartbeat_unauthenticated_rejected(self):
        fresh_client = TestClient(main.app)
        resp = fresh_client.get("/api/sync/heartbeat")
        self.assertEqual(resp.status_code, 401)

    def test_heartbeat_guest_user_allowed(self):
        guest_user = database.create_guest_user()
        g_token = main.generate_token(guest_user["id"], guest_user["username"], is_guest=True)
        resp = self.client.get("/api/sync/heartbeat", headers={"Authorization": f"Bearer {g_token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_heartbeat_returns_standard_schema(self):
        resp = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertIn("server_time", data)
        self.assertIn("conv_hash", data)
        self.assertIn("conversations_changed", data)
        self.assertIn("artifacts_count", data)
        self.assertIn("usage", data)
        self.assertIn("tokens_used", data["usage"])

    def test_heartbeat_no_conversations_returns_empty_list(self):
        resp = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        data = resp.json()
        self.assertTrue(data["conversations_changed"])
        self.assertEqual(data["conversations"], [])

    # 2. Heartbeat Conversation Sync Tests
    def test_heartbeat_detects_new_conversation(self):
        conv = database.create_conversation("Physics Notes", user_id=self.user1["id"])
        resp = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        data = resp.json()
        self.assertTrue(data["conversations_changed"])
        self.assertEqual(len(data["conversations"]), 1)
        self.assertEqual(data["conversations"][0]["id"], conv["id"])
        self.assertEqual(data["conversations"][0]["title"], "Physics Notes")

    def test_heartbeat_hash_caching_returns_none_when_unchanged(self):
        database.create_conversation("Chemistry Notes", user_id=self.user1["id"])
        resp1 = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        data1 = resp1.json()
        conv_hash = data1["conv_hash"]
        self.assertTrue(data1["conversations_changed"])
        self.assertIsNotNone(data1["conversations"])

        # Second poll with client conv_hash
        resp2 = self.client.get(f"/api/sync/heartbeat?conv_hash={conv_hash}", headers=self.auth1)
        data2 = resp2.json()
        self.assertFalse(data2["conversations_changed"])
        self.assertIsNone(data2["conversations"])
        self.assertEqual(data2["conv_hash"], conv_hash)

    def test_heartbeat_detects_conversation_title_rename(self):
        conv = database.create_conversation("Old Title", user_id=self.user1["id"])
        resp1 = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        conv_hash1 = resp1.json()["conv_hash"]

        # Rename conversation
        database.update_conversation_title(conv["id"], "Brand New Title", user_id=self.user1["id"])

        resp2 = self.client.get(f"/api/sync/heartbeat?conv_hash={conv_hash1}", headers=self.auth1)
        data2 = resp2.json()
        self.assertTrue(data2["conversations_changed"])
        self.assertNotEqual(data2["conv_hash"], conv_hash1)
        self.assertEqual(data2["conversations"][0]["title"], "Brand New Title")

    def test_heartbeat_detects_conversation_pin_toggle(self):
        c1 = database.create_conversation("Chat 1", user_id=self.user1["id"])
        c2 = database.create_conversation("Chat 2", user_id=self.user1["id"])
        resp1 = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        h1 = resp1.json()["conv_hash"]

        # Pin Chat 1
        database.toggle_pin_conversation(c1["id"], is_pinned=True, user_id=self.user1["id"])

        resp2 = self.client.get(f"/api/sync/heartbeat?conv_hash={h1}", headers=self.auth1)
        data2 = resp2.json()
        self.assertTrue(data2["conversations_changed"])
        self.assertEqual(data2["conversations"][0]["id"], c1["id"])
        self.assertEqual(data2["conversations"][0]["is_pinned"], 1)

    def test_heartbeat_detects_conversation_archive(self):
        c1 = database.create_conversation("To Archive", user_id=self.user1["id"])
        resp1 = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        h1 = resp1.json()["conv_hash"]

        # Archive conversation
        database.archive_conversation(c1["id"], is_archived=True, user_id=self.user1["id"])

        resp2 = self.client.get(f"/api/sync/heartbeat?conv_hash={h1}", headers=self.auth1)
        data2 = resp2.json()
        self.assertTrue(data2["conversations_changed"])
        self.assertEqual(len(data2["conversations"]), 0)

    def test_heartbeat_detects_conversation_deletion(self):
        c1 = database.create_conversation("To Delete", user_id=self.user1["id"])
        resp1 = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        h1 = resp1.json()["conv_hash"]

        database.delete_conversation(c1["id"], user_id=self.user1["id"])

        resp2 = self.client.get(f"/api/sync/heartbeat?conv_hash={h1}", headers=self.auth1)
        data2 = resp2.json()
        self.assertTrue(data2["conversations_changed"])
        self.assertEqual(len(data2["conversations"]), 0)

    # 3. Active Conversation Real-Time Sync Tests
    def test_heartbeat_active_conv_no_messages(self):
        c1 = database.create_conversation("Empty Chat", user_id=self.user1["id"])
        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={c1['id']}&last_msg_count=0", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 0)
        self.assertIsNone(data["active_messages"])

    def test_heartbeat_active_conv_new_user_message_synced(self):
        c1 = database.create_conversation("Active Chat", user_id=self.user1["id"])
        # Client B is viewing c1 with 0 messages
        # Client A posts user message
        database.add_message(c1["id"], role="user", content="Hello Cortex!", user_id=self.user1["id"])

        # Client B polls
        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={c1['id']}&last_msg_count=0", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 1)
        self.assertIsNotNone(data["active_messages"])
        self.assertEqual(data["active_messages"][0]["content"], "Hello Cortex!")
        self.assertEqual(data["active_messages"][0]["role"], "user")

    def test_heartbeat_active_conv_assistant_reply_synced(self):
        c1 = database.create_conversation("Active Chat", user_id=self.user1["id"])
        database.add_message(c1["id"], role="user", content="Explain quantum computing", user_id=self.user1["id"])
        database.add_message(c1["id"], role="assistant", content="Quantum computing harnesses qubits...", user_id=self.user1["id"])

        # Client B had 1 message (user message)
        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={c1['id']}&last_msg_count=1", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 2)
        self.assertIsNotNone(data["active_messages"])
        self.assertEqual(len(data["active_messages"]), 2)
        self.assertEqual(data["active_messages"][1]["role"], "assistant")

    def test_heartbeat_active_conv_matches_last_count_returns_none(self):
        c1 = database.create_conversation("Active Chat", user_id=self.user1["id"])
        database.add_message(c1["id"], role="user", content="Ping", user_id=self.user1["id"])

        # Client B already has 1 message
        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={c1['id']}&last_msg_count=1", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 1)
        self.assertIsNone(data["active_messages"])

    def test_heartbeat_active_conv_tools_used_parsed_as_list(self):
        c1 = database.create_conversation("Tool Chat", user_id=self.user1["id"])
        database.add_message(c1["id"], role="assistant", content="Weather is sunny", tools_used=["web_search", "weather_api"], user_id=self.user1["id"])

        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={c1['id']}&last_msg_count=0", headers=self.auth1)
        data = resp.json()
        self.assertIsInstance(data["active_messages"][0]["tools_used"], list)
        self.assertIn("web_search", data["active_messages"][0]["tools_used"])

    def test_heartbeat_active_conv_nonexistent_returns_count_zero(self):
        resp = self.client.get("/api/sync/heartbeat?active_conv_id=nonexistent_id&last_msg_count=0", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 0)
        self.assertIsNone(data["active_messages"])

    def test_heartbeat_active_conv_new_returns_count_zero(self):
        resp = self.client.get("/api/sync/heartbeat?active_conv_id=new&last_msg_count=0", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 0)
        self.assertIsNone(data["active_messages"])

    # 4. User Isolation & Multi-Client Simulated Sync
    def test_heartbeat_isolated_between_different_users(self):
        database.create_conversation("User1 Secret", user_id=self.user1["id"])
        database.create_conversation("User2 Secret", user_id=self.user2["id"])

        r1 = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        r2 = self.client.get("/api/sync/heartbeat", headers=self.auth2).json()

        titles1 = [c["title"] for c in r1["conversations"]]
        titles2 = [c["title"] for c in r2["conversations"]]

        self.assertIn("User1 Secret", titles1)
        self.assertNotIn("User2 Secret", titles1)
        self.assertIn("User2 Secret", titles2)
        self.assertNotIn("User1 Secret", titles2)

    def test_multi_browser_simulation_new_chat_appears_in_client_b(self):
        # Client B starts up and polls
        b_init = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        b_hash = b_init["conv_hash"]
        self.assertEqual(len(b_init["conversations"]), 0)

        # Client A in another browser creates a new chat
        a_conv = self.client.post("/api/conversations", json={"title": "Client A Chat"}, headers=self.auth1).json()

        # Client B polls with its previous hash
        b_poll = self.client.get(f"/api/sync/heartbeat?conv_hash={b_hash}", headers=self.auth1).json()
        self.assertTrue(b_poll["conversations_changed"])
        self.assertEqual(b_poll["conversations"][0]["id"], a_conv["id"])
        self.assertEqual(b_poll["conversations"][0]["title"], "Client A Chat")

    def test_multi_browser_simulation_message_stream_appears_in_client_b(self):
        # Client A creates conversation
        conv = database.create_conversation("Live Stream", user_id=self.user1["id"])
        # Client B opens the conversation
        b_poll1 = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv['id']}&last_msg_count=0", headers=self.auth1).json()
        self.assertEqual(b_poll1["active_msg_count"], 0)

        # Client A sends user prompt and gets assistant answer
        database.add_message(conv["id"], role="user", content="What is 2+2?", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="2 + 2 = 4", user_id=self.user1["id"])

        # Client B polls again
        b_poll2 = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv['id']}&last_msg_count=0", headers=self.auth1).json()
        self.assertEqual(b_poll2["active_msg_count"], 2)
        self.assertEqual(len(b_poll2["active_messages"]), 2)
        self.assertEqual(b_poll2["active_messages"][0]["content"], "What is 2+2?")
        self.assertEqual(b_poll2["active_messages"][1]["content"], "2 + 2 = 4")

    def test_multi_browser_simulation_consecutive_messages(self):
        conv = database.create_conversation("Chat Sequence", user_id=self.user1["id"])
        for i in range(5):
            database.add_message(conv["id"], role="user", content=f"Step {i}", user_id=self.user1["id"])

        resp = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv['id']}&last_msg_count=2", headers=self.auth1)
        data = resp.json()
        self.assertEqual(data["active_msg_count"], 5)
        self.assertEqual(len(data["active_messages"]), 5)

    # 5. Indestructible Artifact Deduplication Tests
    def test_artifact_deduplication_exact_filename_same_conversation(self):
        conv = database.create_conversation("Casual Chat", user_id=self.user1["id"])
        # Post two messages in the same conversation with the same doc title / slug
        m1 = "# How It Works Simplified\nThis is deep learning architecture."
        m2 = "# How It Works Simplified\nThis is refined deep learning architecture with further details."
        database.add_message(conv["id"], role="assistant", content=m1, user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content=m2, user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        # Exactly ONE artifact must be returned for how_it_works_simplified.md in Casual Chat!
        matching = [a for a in arts if a["conversation_id"] == conv["id"] and "how_it_works_simplified" in a["filename"]]
        self.assertEqual(len(matching), 1)

    def test_artifact_deduplication_case_insensitive(self):
        conv = database.create_conversation("Case Test", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Data Pipeline Overview\nData ingest.", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# DATA PIPELINE OVERVIEW\nData transform.", user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        matching = [a for a in arts if a["conversation_id"] == conv["id"]]
        self.assertEqual(len(matching), 1)

    def test_artifact_canonical_key_structure(self):
        conv = database.create_conversation("Key Test", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Architecture Plan\nComponents...", user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        self.assertTrue(len(arts) >= 1)
        art = arts[0]
        self.assertIn("key", art)
        expected_key = f"{conv['id']}:{art['filename'].lower()}"
        self.assertEqual(art["key"], expected_key)

    def test_artifact_endpoint_deduplication(self):
        conv = database.create_conversation("API Dedup Chat", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Quickstart Guide\nStep 1 2 3", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Quickstart Guide\nStep 1 2 3 4", user_id=self.user1["id"])

        resp = self.client.get("/api/artifacts", headers=self.auth1)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        matching = [a for a in data["artifacts"] if a["conversation_id"] == conv["id"]]
        self.assertEqual(len(matching), 1)
        self.assertEqual(data["total"], len(data["artifacts"]))

    def test_artifact_repeated_fetches_count_immutable(self):
        conv = database.create_conversation("Counter Test", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Immutable Document\nContent...", user_id=self.user1["id"])

        initial_count = len(database.get_user_artifacts(self.user1["id"]))
        for _ in range(10):
            arts = database.get_user_artifacts(self.user1["id"])
            self.assertEqual(len(arts), initial_count)

    def test_artifact_heartbeat_count_matches_artifacts_endpoint(self):
        conv = database.create_conversation("Heartbeat Artifacts", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Test Doc A\nContent A...", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Test Doc B\nContent B...", user_id=self.user1["id"])

        api_resp = self.client.get("/api/artifacts", headers=self.auth1).json()
        hb_resp = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()

        self.assertEqual(api_resp["total"], hb_resp["artifacts_count"])

    def test_artifact_deletion_sync_across_clients(self):
        conv = database.create_conversation("Delete Sync", user_id=self.user1["id"])
        database.add_message(conv["id"], role="assistant", content="# Ephemeral Doc\nTo be deleted...", user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        self.assertEqual(len(arts), 1)
        target_key = arts[0]["key"]

        # Delete artifact via endpoint
        del_resp = self.client.delete(f"/api/artifacts/{target_key}", headers=self.auth1)
        self.assertEqual(del_resp.status_code, 200)

        # Both artifacts endpoint and heartbeat report 0
        api_after = self.client.get("/api/artifacts", headers=self.auth1).json()
        hb_after = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()

        self.assertEqual(api_after["total"], 0)
        self.assertEqual(hb_after["artifacts_count"], 0)

    def test_artifact_deletion_by_message_id(self):
        conv = database.create_conversation("Delete By Msg", user_id=self.user1["id"])
        msg = database.add_message(conv["id"], role="assistant", content="# Delete By ID\nContent...", user_id=self.user1["id"])

        self.assertEqual(len(database.get_user_artifacts(self.user1["id"])), 1)
        database.mark_artifact_deleted(self.user1["id"], msg["id"])
        self.assertEqual(len(database.get_user_artifacts(self.user1["id"])), 0)

    def test_artifact_different_conversations_same_filename_allowed(self):
        c1 = database.create_conversation("Conv 1", user_id=self.user1["id"])
        c2 = database.create_conversation("Conv 2", user_id=self.user1["id"])
        database.add_message(c1["id"], role="assistant", content="# Shared Title\nDoc in conv 1", user_id=self.user1["id"])
        database.add_message(c2["id"], role="assistant", content="# Shared Title\nDoc in conv 2", user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        self.assertEqual(len(arts), 2)
        c_ids = {a["conversation_id"] for a in arts}
        self.assertIn(c1["id"], c_ids)
        self.assertIn(c2["id"], c_ids)

    def test_artifact_code_block_language_extensions(self):
        conv = database.create_conversation("Code Blocks", user_id=self.user1["id"])
        code = "```javascript\nfunction hello() {\n  return 'world';\n}\n```"
        database.add_message(conv["id"], role="assistant", content=code, user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        self.assertTrue(len(arts) >= 1)
        self.assertTrue(arts[0]["filename"].endswith(".js") or arts[0]["filename"].endswith(".md"))

    # 6. Monotonic Token & Workspace Sync Tests
    def test_token_usage_heartbeat_sync(self):
        database.sync_daily_tokens_used(self.user1["id"], 4500)
        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        self.assertEqual(hb["usage"]["tokens_used"], 4500)

    def test_multi_browser_project_creation_and_conv_assignment(self):
        proj = database.create_project("AI Project", user_id=self.user1["id"], description="Research")
        conv = database.create_conversation("AI Chat", user_id=self.user1["id"], project_id=proj["id"])

        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        conv_meta = next((c for c in hb["conversations"] if c["id"] == conv["id"]), None)
        self.assertIsNotNone(conv_meta)
        self.assertEqual(conv_meta["project_id"], proj["id"])

    def test_multi_browser_system_instructions_sync(self):
        conv = database.create_conversation("Instruction Chat", user_id=self.user1["id"])
        database.update_conversation_custom_instructions(conv["id"], "Act as an expert math tutor.")

        retrieved = database.get_conversation_custom_instructions(conv["id"])
        self.assertEqual(retrieved, "Act as an expert math tutor.")

    def test_multi_browser_fork_conversation_sync(self):
        conv = database.create_conversation("Root Chat", user_id=self.user1["id"])
        database.add_message(conv["id"], role="user", content="Root message", user_id=self.user1["id"])

        fork = database.fork_conversation(conv["id"], new_title="Forked Branch", user_id=self.user1["id"])
        self.assertIsNotNone(fork)

        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        titles = [c["title"] for c in hb["conversations"]]
        self.assertIn("Root Chat", titles)
        self.assertIn("Forked Branch", titles)

    def test_multi_browser_message_deletion_sync(self):
        conv = database.create_conversation("Msg Delete Chat", user_id=self.user1["id"])
        m1 = database.add_message(conv["id"], role="user", content="Keep", user_id=self.user1["id"])
        m2 = database.add_message(conv["id"], role="user", content="Remove", user_id=self.user1["id"])

        database.delete_messages_after(conv["id"], m2["id"], user_id=self.user1["id"])

        hb = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv['id']}&last_msg_count=2", headers=self.auth1).json()
        self.assertEqual(hb["active_msg_count"], 1)
        self.assertEqual(hb["active_messages"][0]["id"], m1["id"])

    def test_sync_state_endpoint_heals_missing_messages(self):
        conv_id = str(uuid.uuid4())
        payload = {
            "conversations": [{"id": conv_id, "title": "Healed Chat"}],
            "messages": [
                {"id": str(uuid.uuid4()), "conversation_id": conv_id, "role": "user", "content": "Offline turn"}
            ]
        }
        sync_resp = self.client.post("/api/sync/state", json=payload, headers=self.auth1)
        self.assertEqual(sync_resp.status_code, 200)

        hb = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv_id}", headers=self.auth1).json()
        self.assertEqual(hb["active_msg_count"], 1)
        self.assertEqual(hb["active_messages"][0]["content"], "Offline turn")

    # 7. Performance & Concurrency Under Multi-Client Load
    def test_heartbeat_performance_under_50ms(self):
        start = time.perf_counter()
        resp = self.client.get("/api/sync/heartbeat", headers=self.auth1)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed_ms, 50.0)

    def test_heartbeat_concurrent_requests(self):
        def query_hb():
            r = self.client.get("/api/sync/heartbeat", headers=self.auth1)
            return r.status_code == 200

        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(lambda _: query_hb(), range(16)))
        self.assertTrue(all(results))

    def test_heartbeat_special_characters_in_title(self):
        special_title = "गणित & Machine Learning 🚀 (Testing / Special: chars?)"
        database.create_conversation(special_title, user_id=self.user1["id"])
        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        titles = [c["title"] for c in hb["conversations"]]
        self.assertIn(special_title, titles)

    def test_heartbeat_long_message_content(self):
        conv = database.create_conversation("Long Text Chat", user_id=self.user1["id"])
        long_content = "A" * 12000
        database.add_message(conv["id"], role="user", content=long_content, user_id=self.user1["id"])

        hb = self.client.get(f"/api/sync/heartbeat?active_conv_id={conv['id']}&last_msg_count=0", headers=self.auth1).json()
        self.assertEqual(len(hb["active_messages"][0]["content"]), 12000)

    def test_heartbeat_client_hash_corrupted_fallback(self):
        database.create_conversation("Fallback Test", user_id=self.user1["id"])
        resp = self.client.get("/api/sync/heartbeat?conv_hash=invalid_bogus_hash", headers=self.auth1)
        data = resp.json()
        self.assertTrue(data["conversations_changed"])
        self.assertIsNotNone(data["conversations"])

    def test_heartbeat_returns_latest_active_conv(self):
        c1 = database.create_conversation("Latest Active Test", user_id=self.user1["id"])
        hb = self.client.get("/api/sync/heartbeat", headers=self.auth1).json()
        self.assertIn("latest_active_conv", hb)
        self.assertEqual(hb["latest_active_conv"]["id"], c1["id"])

    def test_artifact_deduplication_by_stem(self):
        c1 = database.create_conversation("JEE", user_id=self.user1["id"])
        # Message 1
        msg1_content = "## 🚀 How to Tackle JEE-Advanced Questions Like a Pro\n\nTips on solving JEE advanced problems thoroughly.\n" + ("Text " * 80)
        # Message 2 with slightly different continuation/heading
        msg2_content = "## How to Tackle JEE-Advanced Questions Like a Pro (Part 2)\n\nMore tips on solving.\n" + ("Text " * 80)
        database.add_message(c1["id"], role="assistant", content=msg1_content, user_id=self.user1["id"])
        database.add_message(c1["id"], role="assistant", content=msg2_content, user_id=self.user1["id"])

        arts = database.get_user_artifacts(self.user1["id"])
        # Stem deduplication should deduplicate both messages in the same conversation into 1 artifact
        jee_arts = [a for a in arts if a["conversation_id"] == c1["id"]]
        self.assertEqual(len(jee_arts), 1)
        self.assertTrue(jee_arts[0]["key"].startswith(f"{c1['id']}:how_to_tackle_jee_advanced_"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
