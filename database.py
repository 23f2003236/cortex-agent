import hashlib
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent / "cortex.db"
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Return a thread-local SQLite connection with WAL mode and foreign keys enabled."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        _local.conn = conn
    return conn


CURRENT_SCHEMA_VERSION = 3


def init_db() -> None:
    """Initialize database tables for users, conversations, and messages."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_guest INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tools_used TEXT,
                feedback INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'preference',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_created ON projects(user_id, created_at)")

        # Migrate existing conversations table if user_id, is_pinned, custom_instructions, or project_id column is missing
        conv_cols = [r["name"] for r in conn.execute("PRAGMA table_info(conversations)").fetchall()]
        if "user_id" not in conv_cols:
            conn.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT REFERENCES users(id) ON DELETE CASCADE")
        if "is_pinned" not in conv_cols:
            conn.execute("ALTER TABLE conversations ADD COLUMN is_pinned INTEGER DEFAULT 0")
        if "custom_instructions" not in conv_cols:
            conn.execute("ALTER TABLE conversations ADD COLUMN custom_instructions TEXT DEFAULT ''")
        if "project_id" not in conv_cols:
            conn.execute("ALTER TABLE conversations ADD COLUMN project_id TEXT DEFAULT NULL REFERENCES projects(id) ON DELETE SET NULL")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(project_id)")

        # Migrate existing users table for custom_instructions and is_guest
        user_cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "custom_instructions" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN custom_instructions TEXT DEFAULT ''")
        if "is_guest" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN is_guest INTEGER DEFAULT 0")

        # Migrate existing messages table for feedback column
        msg_cols = [r["name"] for r in conn.execute("PRAGMA table_info(messages)").fetchall()]
        if "feedback" not in msg_cols:
            conn.execute("ALTER TABLE messages ADD COLUMN feedback INTEGER DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_usage (
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                usage_date TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                uploads_count INTEGER DEFAULT 0,
                reserved_tokens INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, usage_date)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_usage_user ON daily_usage(user_id, usage_date)")

        # Migration: ensure reserved_tokens column exists on existing databases
        try:
            conn.execute("ALTER TABLE daily_usage ADD COLUMN reserved_tokens INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                token_sig TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                revoked_at TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_revoked_tokens_exp ON revoked_tokens(expires_at)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )

        current_v = 0
        try:
            r = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
            current_v = int(r["v"]) if r and r["v"] is not None else 0
        except sqlite3.OperationalError:
            pass

        now_iso = _utc_now_iso()
        if current_v < 1:
            conn.execute("INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (1, ?, 'Initial schema with users, conversations, messages, artifacts, memories, projects')", (now_iso,))
        if current_v < 2:
            conn.execute("INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (2, ?, 'Guest accounts, token revocation, message feedback')", (now_iso,))
        if current_v < 3:
            conn.execute("INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (3, ?, 'Atomic quota reservation with reserved_tokens')", (now_iso,))

        conn.commit()


def get_schema_version() -> int:
    """Return the highest applied schema migration version."""
    with get_connection() as conn:
        try:
            row = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
            return int(row["v"]) if row and row["v"] is not None else 0
        except sqlite3.OperationalError:
            return 0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------- Auth & User Management ----------------

DEFAULT_PBKDF2_ROUNDS = 600_000
LEGACY_PBKDF2_ROUNDS = 100_000


def hash_password(password: str, salt: Optional[str] = None, iterations: Optional[int] = None) -> tuple[str, str]:
    if not salt:
        rounds = iterations or DEFAULT_PBKDF2_ROUNDS
        raw_salt = secrets.token_hex(16)
        formatted_salt = f"{raw_salt}${rounds}"
    elif "$" in salt:
        raw_salt, iter_str = salt.split("$", 1)
        rounds = int(iter_str)
        formatted_salt = salt
    else:
        raw_salt = salt
        rounds = iterations or LEGACY_PBKDF2_ROUNDS
        formatted_salt = salt

    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        raw_salt.encode("utf-8"),
        rounds,
    ).hex()
    return pw_hash, formatted_salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, password_hash)


def create_user(username: str, password: str, email: Optional[str] = None) -> dict[str, Any]:
    username_clean = username.strip().lower()
    if not username_clean:
        raise ValueError("Username cannot be empty.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    pw_hash, salt = hash_password(password)
    user_id = str(uuid.uuid4())
    now = _utc_now_iso()

    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, salt, created_at, is_guest) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (user_id, username_clean, (email or "").strip(), pw_hash, salt, now),
            )
            # If this is the first registered user, auto-assign any orphan conversations
            count_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_guest = 0").fetchone()["c"]
            if count_users == 1:
                conn.execute("UPDATE conversations SET user_id = ? WHERE user_id IS NULL", (user_id,))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Username '{username_clean}' is already registered.")

    return {
        "id": user_id,
        "username": username_clean,
        "email": (email or "").strip(),
        "is_guest": False,
        "created_at": now,
    }


def authenticate_user(username: str, password: str) -> Optional[dict[str, Any]]:
    username_clean = username.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash, salt, created_at, is_guest FROM users WHERE username = ?",
            (username_clean,),
        ).fetchone()
        if not row:
            return None
        if verify_password(password, row["password_hash"], row["salt"]):
            # Transparently upgrade legacy 100k hashes to 600k rounds on login
            if "$" not in (row["salt"] or ""):
                new_hash, new_salt = hash_password(password)
                conn.execute(
                    "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                    (new_hash, new_salt, row["id"]),
                )
                conn.commit()

            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "is_guest": bool(row["is_guest"]),
                "created_at": row["created_at"],
            }
        return None


def create_guest_user() -> dict[str, Any]:
    """Create an anonymous, isolated ephemeral guest account."""
    uid = str(uuid.uuid4())
    guest_suffix = uid[:8]
    username = f"guest_{guest_suffix}"
    raw_pwd = secrets.token_urlsafe(24)
    pw_hash, salt = hash_password(raw_pwd)
    now = _utc_now_iso()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, salt, created_at, is_guest) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (uid, username, "", pw_hash, salt, now),
        )
        conn.commit()

    return {
        "id": uid,
        "username": username,
        "email": "",
        "is_guest": True,
        "created_at": now,
    }


def get_user_by_id(user_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at, is_guest FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_guest"] = bool(d.get("is_guest", 0))
        return d


def get_user_by_username(username: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at, is_guest FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_guest"] = bool(d.get("is_guest", 0))
        return d


def revoke_token(token_sig: str, user_id: str, expires_at: Optional[int] = None) -> None:
    """Blacklist a token signature until its natural expiration."""
    exp = int(expires_at) if expires_at is not None else int(time.time()) + 86400 * 30
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO revoked_tokens (token_sig, user_id, revoked_at, expires_at) VALUES (?, ?, ?, ?)",
            (token_sig, user_id, _utc_now_iso(), exp),
        )
        # Prune already-expired revoked tokens
        conn.execute("DELETE FROM revoked_tokens WHERE expires_at < ?", (int(time.time()),))
        conn.commit()


def is_token_revoked(token_sig: str) -> bool:
    """Check if a token signature has been revoked."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM revoked_tokens WHERE token_sig = ?",
            (token_sig,),
        ).fetchone()
        return row is not None


# ---------------- Conversation Management ----------------

def create_conversation(
    title: str = "New Chat",
    conv_id: Optional[str] = None,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> dict[str, Any]:
    cid = conv_id or str(uuid.uuid4())
    now = _utc_now_iso()
    with get_connection() as conn:
        valid_project_id = None
        if project_id and user_id:
            chk = conn.execute("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)).fetchone()
            if chk:
                valid_project_id = project_id
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at, user_id, project_id) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, title, now, now, user_id, valid_project_id),
        )
        conn.commit()
    return {"id": cid, "title": title, "created_at": now, "updated_at": now, "user_id": user_id, "project_id": valid_project_id}


def get_conversations(user_id: Optional[str] = None, project_id: Optional[str] = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cols = "id, title, created_at, updated_at, user_id, project_id, COALESCE(is_pinned, 0) as is_pinned"
        if user_id and project_id:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE user_id = ? AND project_id = ? ORDER BY is_pinned DESC, updated_at DESC",
                (user_id, project_id),
            )
        elif user_id:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE user_id = ? ORDER BY is_pinned DESC, updated_at DESC",
                (user_id,),
            )
        else:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations ORDER BY is_pinned DESC, updated_at DESC"
            )
        return [dict(row) for row in cursor.fetchall()]


def get_conversation(conv_id: str, user_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        cols = "id, title, created_at, updated_at, user_id, project_id, COALESCE(is_pinned, 0) as is_pinned"
        if user_id:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE id = ? AND user_id = ?",
                (conv_id, user_id),
            )
        else:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE id = ?",
                (conv_id,),
            )
        row = cursor.fetchone()
        return dict(row) if row else None


def toggle_pin_conversation(conv_id: str, is_pinned: Optional[bool] = None, user_id: Optional[str] = None) -> Optional[bool]:
    with get_connection() as conn:
        query_sel = "SELECT COALESCE(is_pinned, 0) as is_pinned FROM conversations WHERE id = ?"
        params_sel = [conv_id]
        if user_id:
            query_sel += " AND user_id = ?"
            params_sel.append(user_id)

        cur = conn.execute(query_sel, tuple(params_sel))
        row = cur.fetchone()
        if not row:
            return None

        if is_pinned is None:
            new_val = 0 if row["is_pinned"] else 1
        else:
            new_val = 1 if is_pinned else 0

        now = _utc_now_iso()
        query_upd = "UPDATE conversations SET is_pinned = ?, updated_at = ? WHERE id = ?"
        params_upd = [new_val, now, conv_id]
        if user_id:
            query_upd += " AND user_id = ?"
            params_upd.append(user_id)

        cursor = conn.execute(query_upd, tuple(params_upd))
        conn.commit()
        return bool(new_val) if cursor.rowcount > 0 else None


def update_conversation_title(conv_id: str, title: str, user_id: Optional[str] = None) -> bool:
    now = _utc_now_iso()
    with get_connection() as conn:
        if user_id:
            cursor = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (title, now, conv_id, user_id),
            )
        else:
            cursor = conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id),
            )
        conn.commit()
        return cursor.rowcount > 0


def delete_conversation(conv_id: str, user_id: Optional[str] = None) -> bool:
    with get_connection() as conn:
        if user_id:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conv_id, user_id),
            )
        else:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_messages(conv_id: str, user_id: Optional[str] = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if user_id:
            chk = conn.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id)).fetchone()
            if not chk:
                return []
        cursor = conn.execute(
            "SELECT id, conversation_id, role, content, tools_used, feedback, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        )
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            if item.get("tools_used"):
                try:
                    item["tools_used"] = json.loads(item["tools_used"])
                except Exception:
                    item["tools_used"] = []
            else:
                item["tools_used"] = []
            item["feedback"] = item.get("feedback") if item.get("feedback") is not None else 0
            results.append(item)
        return results


def add_message(
    conv_id: str,
    role: str,
    content: str,
    tools_used: Optional[list[str]] = None,
    msg_id: Optional[str] = None,
    user_id: Optional[str] = None,
    feedback: int = 0,
) -> dict[str, Any]:
    mid = msg_id or str(uuid.uuid4())
    now = _utc_now_iso()
    tools_json = json.dumps(tools_used or []) if tools_used else None

    with get_connection() as conn:
        # Ensure conversation exists; if not, create it
        cur = conn.execute("SELECT id, user_id FROM conversations WHERE id = ?", (conv_id,))
        conv_row = cur.fetchone()
        if not conv_row:
            default_title = "New Chat"
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, ?)",
                (conv_id, default_title, now, now, user_id),
            )
        else:
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conv_id),
            )

        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, tools_used, feedback, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mid, conv_id, role, content, tools_json, feedback, now),
        )
        conn.commit()

    return {
        "id": mid,
        "conversation_id": conv_id,
        "role": role,
        "content": content,
        "tools_used": tools_used or [],
        "feedback": feedback,
        "created_at": now,
    }


def delete_messages_after(conv_id: str, message_id: str, user_id: Optional[str] = None) -> bool:
    """Delete the specified message and all messages that came after it (used for retries & branching)."""
    with get_connection() as conn:
        if user_id:
            chk = conn.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id)).fetchone()
            if not chk:
                return False
        cur = conn.execute(
            "SELECT created_at FROM messages WHERE id = ? AND conversation_id = ?",
            (message_id, conv_id),
        )
        row = cur.fetchone()
        if not row:
            return False
        cutoff_time = row["created_at"]
        conn.execute(
            "DELETE FROM messages WHERE conversation_id = ? AND created_at >= ?",
            (conv_id, cutoff_time),
        )
        now = _utc_now_iso()
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conv_id),
        )
        conn.commit()
        return True


def set_message_feedback(message_id: str, feedback: int, user_id: Optional[str] = None) -> bool:
    """Update thumbs up (1) / thumbs down (-1) / neutral (0) feedback for a message."""
    if feedback not in (-1, 0, 1):
        return False
    with get_connection() as conn:
        if user_id:
            cur = conn.execute(
                """
                SELECT m.id FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.id = ? AND c.user_id = ?
                """,
                (message_id, user_id),
            )
            if not cur.fetchone():
                return False
        cursor = conn.execute("UPDATE messages SET feedback = ? WHERE id = ?", (feedback, message_id))
        conn.commit()
        return cursor.rowcount > 0


def fork_conversation(
    conv_id: str,
    up_to_message_id: Optional[str] = None,
    user_id: str = "",
    new_title: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Fork a conversation up to a specified message into a brand new conversation."""
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conv_row = cur.fetchone()
        if not conv_row:
            return None

        # Fetch messages up to cutoff if specified, else all messages
        if up_to_message_id:
            cur_msg = conn.execute(
                "SELECT created_at FROM messages WHERE id = ? AND conversation_id = ?",
                (up_to_message_id, conv_id),
            )
            msg_row = cur_msg.fetchone()
            if not msg_row:
                return None
            cutoff_time = msg_row["created_at"]
            cur_msgs = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? AND created_at <= ? ORDER BY created_at ASC",
                (conv_id, cutoff_time),
            )
        else:
            cur_msgs = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conv_id,),
            )
        history_rows = cur_msgs.fetchall()

        new_conv_id = str(uuid.uuid4())
        now = _utc_now_iso()
        title = new_title or f"[Fork] {conv_row['title']}"
        custom_instr = conv_row["custom_instructions"] if "custom_instructions" in conv_row.keys() else ""

        conn.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at, user_id, is_pinned, custom_instructions)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (new_conv_id, title, now, now, user_id, custom_instr),
        )

        cloned_messages = []
        for row in history_rows:
            new_mid = str(uuid.uuid4())
            feedback_val = row["feedback"] if "feedback" in row.keys() and row["feedback"] is not None else 0
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, tools_used, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_mid, new_conv_id, row["role"], row["content"], row["tools_used"], feedback_val, row["created_at"]),
            )
            tools_parsed = []
            if row["tools_used"]:
                try:
                    tools_parsed = json.loads(row["tools_used"])
                except Exception:
                    tools_parsed = []
            cloned_messages.append({
                "id": new_mid,
                "conversation_id": new_conv_id,
                "role": row["role"],
                "content": row["content"],
                "tools_used": tools_parsed,
                "feedback": feedback_val,
                "created_at": row["created_at"],
            })

        conn.commit()

        conv_dict = {
            "id": new_conv_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "user_id": user_id,
            "is_pinned": 0,
            "custom_instructions": custom_instr,
        }

        return {
            **conv_dict,
            "conversation": conv_dict,
            "messages": cloned_messages,
        }


# ---------------- Memories & Custom Instructions ----------------

def add_memory(user_id: str, content: str, category: str = "preference") -> dict[str, Any]:
    """Add a new persistent memory for a user."""
    mem_id = str(uuid.uuid4())
    now = _utc_now_iso()
    cat = (category or "preference").strip().lower()
    clean_content = content.strip()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO memories (id, user_id, content, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (mem_id, user_id, clean_content, cat, now, now),
        )
        conn.commit()
    return {
        "id": mem_id,
        "user_id": user_id,
        "content": clean_content,
        "category": cat,
        "created_at": now,
        "updated_at": now,
    }


def get_memories(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch all memories for a user, sorted newest first."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, user_id, content, category, created_at, updated_at FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def delete_memory(memory_id: str, user_id: str) -> bool:
    """Delete a specific memory belonging to a user."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def clear_memories(user_id: str) -> bool:
    """Clear all memories belonging to a user."""
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0


def get_user_custom_instructions(user_id: str) -> str:
    """Get global custom instructions for a user."""
    with get_connection() as conn:
        cur = conn.execute("SELECT custom_instructions FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return (row["custom_instructions"] or "") if row else ""


def update_user_custom_instructions(user_id: str, instructions: str) -> bool:
    """Update global custom instructions for a user."""
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET custom_instructions = ? WHERE id = ?",
            (instructions.strip(), user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_conversation_custom_instructions(conv_id: str) -> str:
    """Get conversation-level custom instructions."""
    with get_connection() as conn:
        cur = conn.execute("SELECT custom_instructions FROM conversations WHERE id = ?", (conv_id,))
        row = cur.fetchone()
        return (row["custom_instructions"] or "") if row else ""


def update_conversation_custom_instructions(conv_id: str, instructions: str) -> bool:
    """Update conversation-level custom instructions."""
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE conversations SET custom_instructions = ?, updated_at = ? WHERE id = ?",
            (instructions.strip(), _utc_now_iso(), conv_id),
        )
        conn.commit()
        return cur.rowcount > 0


# ---------------- Project Workspaces ----------------

def create_project(
    name: str,
    description: str = "",
    system_prompt: str = "",
    user_id: str = "",
) -> dict[str, Any]:
    pid = str(uuid.uuid4())
    now = _utc_now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO projects (id, name, description, system_prompt, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (pid, name.strip(), description.strip(), system_prompt.strip(), user_id, now, now),
        )
        conn.commit()
    return {
        "id": pid,
        "name": name.strip(),
        "description": description.strip(),
        "system_prompt": system_prompt.strip(),
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
    }


def get_projects(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, name, description, system_prompt, user_id, created_at, updated_at FROM projects WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def get_project(project_id: str, user_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, name, description, system_prompt, user_id, created_at, updated_at FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_project(
    project_id: str,
    name: str,
    description: str = "",
    system_prompt: str = "",
    user_id: str = "",
) -> bool:
    now = _utc_now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, system_prompt = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (name.strip(), description.strip(), system_prompt.strip(), now, project_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


def delete_project(project_id: str, user_id: str) -> bool:
    with get_connection() as conn:
        # Unlink conversations first
        conn.execute("UPDATE conversations SET project_id = NULL WHERE project_id = ? AND user_id = ?", (project_id, user_id))
        cur = conn.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        conn.commit()
        return cur.rowcount > 0


def set_conversation_project(conv_id: str, project_id: Optional[str], user_id: str) -> bool:
    with get_connection() as conn:
        if project_id:
            chk = conn.execute("SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)).fetchone()
            if not chk:
                return False
        cur = conn.execute(
            "UPDATE conversations SET project_id = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (project_id, _utc_now_iso(), conv_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0


# ---------------- Daily Usage & Token Quotas ----------------

DAILY_TOKEN_LIMIT = 100_000
DAILY_UPLOAD_LIMIT = 10
GUEST_DAILY_TOKEN_LIMIT = 25_000
GUEST_DAILY_UPLOAD_LIMIT = 3


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_daily_usage(user_id: str, date_str: Optional[str] = None) -> dict:
    d = date_str or _today_str()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT tokens_used, uploads_count, reserved_tokens FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, d),
        ).fetchone()
        tokens_used = int(row["tokens_used"]) if row else 0
        uploads_count = int(row["uploads_count"]) if row else 0
        reserved_tokens = int(row["reserved_tokens"]) if (row and "reserved_tokens" in row.keys() and row["reserved_tokens"] is not None) else 0

        # Check if user is a guest account
        u_row = conn.execute("SELECT is_guest FROM users WHERE id = ?", (user_id,)).fetchone()
        is_guest = bool(u_row and u_row["is_guest"])
        tok_limit = GUEST_DAILY_TOKEN_LIMIT if is_guest else DAILY_TOKEN_LIMIT
        up_limit = GUEST_DAILY_UPLOAD_LIMIT if is_guest else DAILY_UPLOAD_LIMIT

        return {
            "user_id": user_id,
            "date": d,
            "tokens_used": tokens_used,
            "reserved_tokens": reserved_tokens,
            "tokens_limit": tok_limit,
            "uploads_count": uploads_count,
            "uploads_limit": up_limit,
            "tokens_remaining": max(0, tok_limit - (tokens_used + reserved_tokens)),
            "uploads_remaining": max(0, up_limit - uploads_count),
        }


def reserve_quota(user_id: str, estimated_tokens: int = 1500) -> tuple[bool, int, int]:
    """Atomically reserve quota before streaming starts to prevent concurrent quota bypass."""
    if estimated_tokens <= 0:
        estimated_tokens = 500
    d = _today_str()
    with get_connection() as conn:
        u_row = conn.execute("SELECT is_guest FROM users WHERE id = ?", (user_id,)).fetchone()
        is_guest = bool(u_row and u_row["is_guest"])
        tok_limit = GUEST_DAILY_TOKEN_LIMIT if is_guest else DAILY_TOKEN_LIMIT

        row = conn.execute(
            "SELECT tokens_used, reserved_tokens FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, d),
        ).fetchone()
        tokens_used = int(row["tokens_used"]) if row else 0
        reserved_tokens = int(row["reserved_tokens"]) if (row and "reserved_tokens" in row.keys() and row["reserved_tokens"] is not None) else 0

        if (tokens_used + reserved_tokens + estimated_tokens) > tok_limit:
            return False, tokens_used + reserved_tokens, tok_limit

        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count, reserved_tokens)
            VALUES (?, ?, 0, 0, ?)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            reserved_tokens = reserved_tokens + excluded.reserved_tokens
            """,
            (user_id, d, int(estimated_tokens)),
        )
        conn.commit()
        return True, tokens_used + reserved_tokens + estimated_tokens, tok_limit


def release_quota(user_id: str, estimated_tokens: int, actual_tokens: int = 0) -> dict:
    """Atomically release reserved quota and commit actual consumed tokens."""
    d = _today_str()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count, reserved_tokens)
            VALUES (?, ?, ?, 0, 0)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            reserved_tokens = MAX(0, reserved_tokens - ?),
            tokens_used = tokens_used + ?
            """,
            (user_id, d, max(0, int(actual_tokens)), max(0, int(estimated_tokens)), max(0, int(actual_tokens))),
        )
        conn.commit()
    return get_daily_usage(user_id)


def increment_daily_tokens(user_id: str, tokens: int) -> dict:
    if tokens <= 0:
        return get_daily_usage(user_id)
    d = _today_str()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            tokens_used = tokens_used + excluded.tokens_used
            """,
            (user_id, d, int(tokens)),
        )
        conn.commit()
    return get_daily_usage(user_id)


def set_daily_tokens(user_id: str, tokens: int, date_str: Optional[str] = None) -> dict:
    d = date_str or _today_str()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            tokens_used = excluded.tokens_used
            """,
            (user_id, d, max(0, int(tokens))),
        )
        conn.commit()
    return get_daily_usage(user_id, d)


def increment_daily_uploads(user_id: str, count: int = 1) -> dict:
    if count <= 0:
        return get_daily_usage(user_id)
    d = _today_str()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            uploads_count = uploads_count + excluded.uploads_count
            """,
            (user_id, d, int(count)),
        )
        conn.commit()
    return get_daily_usage(user_id)


def check_daily_tokens(user_id: str, additional: int = 1) -> tuple[bool, int, int]:
    usage = get_daily_usage(user_id)
    total_active = usage["tokens_used"] + usage.get("reserved_tokens", 0)
    is_allowed = (total_active + additional) <= usage["tokens_limit"]
    return is_allowed, total_active, usage["tokens_limit"]


def check_daily_uploads(user_id: str, additional: int = 1) -> tuple[bool, int, int]:
    usage = get_daily_usage(user_id)
    is_allowed = (usage["uploads_count"] + additional) <= usage["uploads_limit"]
    return is_allowed, usage["uploads_count"], usage["uploads_limit"]


# ---------------- Claude-Style Artifacts Harvesting ----------------

def is_continuation_prompt(text: str) -> bool:
    """Check if a prompt is requesting the LLM to resume/continue a cut-off response."""
    if not text:
        return False
    t = text.strip().lower()
    if "please continue directly from where you left off" in t:
        return True
    if re.search(r"^(?:continue|carry on|continue generating|keep going|aage bolo|aage batao|next)\b", t):
        return True
    return False


def extract_document_title(text: str, conv_title: str = "") -> str:
    """Extract a human-friendly document title from markdown, ignoring code comments and dividers."""
    # 1. Strip markdown code blocks so comments like '# ---' aren't picked as headings
    text_without_code = re.sub(r"```[\s\S]*?```", "", text)
    lines = text_without_code.split("\n")
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue
        is_heading = bool(re.match(r"^#{1,3}\s+", trimmed))
        is_bold_title = trimmed.startswith("**") and trimmed.endswith("**") and 4 < len(trimmed) < 80
        if is_heading or is_bold_title:
            raw_title = re.sub(r"^#{1,3}\s+", "", trimmed)
            raw_title = re.sub(r"^\*\*|\*\*$", "", raw_title).strip()
            # Ignore separators or dashes
            if re.match(r"^[-_#=\*\s]+$", raw_title):
                continue
            # Remove markdown formatting characters
            clean_title = re.sub(r"[`*_\~#]+", "", raw_title).strip()
            if len(clean_title) >= 3:
                return clean_title[:80]

    # 2. Check for attached document indicator
    doc_m = re.search(r"\[Attached Document:\s*([^\]]+)\]", text)
    if doc_m:
        return doc_m.group(1).strip()[:80]

    return (conv_title or "Generated Document")[:80]


def get_user_artifacts(user_id: str) -> list[dict]:
    """Scan and return all markdown documents, code files, and reports across user conversations,
    seamlessly stitching multi-turn continuation chunks into unified complete artifacts."""
    artifacts = []
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.id, m.conversation_id, m.role, m.content, m.created_at, c.title as conv_title
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
            ORDER BY m.conversation_id, m.created_at ASC
            """,
            (user_id,),
        ).fetchall()

        # Stitch continuation assistant messages into their parent message
        stitched_messages = []
        last_user_prompt = ""

        for r in rows:
            role = r["role"]
            content = (r["content"] or "").strip()
            if role == "user":
                last_user_prompt = content
            elif role == "assistant":
                if (
                    is_continuation_prompt(last_user_prompt)
                    and stitched_messages
                    and stitched_messages[-1]["conversation_id"] == r["conversation_id"]
                ):
                    # Seamlessly stitch continuation content
                    stitched_messages[-1]["content"] += "\n\n" + content
                    stitched_messages[-1]["created_at"] = r["created_at"]
                    stitched_messages[-1]["id"] = r["id"]
                else:
                    stitched_messages.append(dict(r))
                last_user_prompt = ""

        # Process newest first
        stitched_messages.reverse()

        seen_titles = set()
        for item in stitched_messages:
            text = (item["content"] or "").strip()
            if not text:
                continue

            text_without_code = re.sub(r"```[\s\S]*?```", "", text)
            has_heading = bool(re.search(r"^#{1,3}\s+\S+", text_without_code, re.MULTILINE))
            has_doc_attach = "[Attached Document:" in text or "[Structured Tabular Data:" in text
            has_table = "| --- |" in text or "|:---:|" in text
            has_code = "```python" in text or "```javascript" in text or "```html" in text or "```sql" in text

            is_artifact = (
                has_heading
                or has_doc_attach
                or (has_table and len(text) > 300)
                or (has_code and len(text) > 400)
                or len(text) > 600
            )
            if not is_artifact:
                continue

            title = extract_document_title(text, item["conv_title"])
            if title in seen_titles:
                continue
            seen_titles.add(title)

            # Generate safe slug without leading/trailing underscores or emojis
            clean_title_ascii = re.sub(r"[^\w\s-]", "", title).strip()
            safe_slug = re.sub(r"[-\s]+", "_", clean_title_ascii.lower()).strip("_")
            if not safe_slug or len(safe_slug) < 3:
                safe_slug = "document"
            if not safe_slug.endswith(".md"):
                safe_slug += ".md"

            size_bytes = len(text.encode("utf-8"))

            artifacts.append({
                "id": item["id"],
                "conversation_id": item["conversation_id"],
                "conversation_title": item["conv_title"] or "Chat",
                "title": title,
                "filename": safe_slug,
                "content": text,
                "size_bytes": size_bytes,
                "created_at": item["created_at"],
            })

    return artifacts


# Automatically initialize schema on import
init_db()
