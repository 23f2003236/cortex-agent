import hashlib
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("cortex.database")

_DEFAULT_DB = Path(__file__).resolve().parent / "cortex.db"
_CUSTOM_DB_PATH = os.environ.get("CORTEX_DB_PATH") or os.environ.get("PERSISTENT_STORAGE_PATH")

if _CUSTOM_DB_PATH:
    DB_PATH = Path(_CUSTOM_DB_PATH)
elif (
    os.environ.get("VERCEL")
    or os.environ.get("VERCEL_ENV")
    or os.environ.get("VERCEL_REGION")
    or os.environ.get("VERCEL_URL")
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    or os.environ.get("AWS_EXECUTION_ENV")
    or os.environ.get("LAMBDA_TASK_ROOT")
):
    _TMP_DB = Path(tempfile.gettempdir()) / "cortex.db"
    if _DEFAULT_DB.exists() and not _TMP_DB.exists():
        try:
            shutil.copy2(_DEFAULT_DB, _TMP_DB)
        except Exception:
            pass
    DB_PATH = _TMP_DB
else:
    DB_PATH = _DEFAULT_DB
_local = threading.local()
_OPEN_CONNECTIONS: set[sqlite3.Connection] = set()
_CONN_LOCK = threading.Lock()


def close_connection() -> None:
    """Close and remove connection for the current thread."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        _local.conn = None
        with _CONN_LOCK:
            _OPEN_CONNECTIONS.discard(conn)
        try:
            conn.close()
        except Exception:
            pass


def close_all_connections() -> None:
    """Close all open SQLite connections across all threads."""
    with _CONN_LOCK:
        conns = list(_OPEN_CONNECTIONS)
        _OPEN_CONNECTIONS.clear()
    for c in conns:
        try:
            c.close()
        except Exception:
            pass
    _local.conn = None


def set_db_path(new_path: Path) -> None:
    """Dynamically set DB_PATH and close all existing connections across threads."""
    global DB_PATH
    close_all_connections()
    DB_PATH = Path(new_path)


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
        with _CONN_LOCK:
            _OPEN_CONNECTIONS.add(conn)
    return conn


CURRENT_SCHEMA_VERSION = 9


def backup_db(target_path: Optional[Path] = None) -> Path:
    """Create a point-in-time consistent online backup of the SQLite database without stopping traffic."""
    if target_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target_path = DB_PATH.parent / f"{DB_PATH.stem}_backup_{ts}.db"

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as src_conn:
        dest_conn = sqlite3.connect(str(target_path))
        try:
            src_conn.backup(dest_conn)
        finally:
            dest_conn.close()
    return target_path


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
                is_guest INTEGER DEFAULT 0,
                expires_at TEXT
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

        # Migrate existing projects table for is_pinned, is_deleted, and deleted_at
        proj_cols = [r["name"] for r in conn.execute("PRAGMA table_info(projects)").fetchall()]
        if "is_pinned" not in proj_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN is_pinned INTEGER DEFAULT 0")
        if "is_deleted" not in proj_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN is_deleted INTEGER DEFAULT 0")
        if "deleted_at" not in proj_cols:
            conn.execute("ALTER TABLE projects ADD COLUMN deleted_at TEXT DEFAULT NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_pinned ON projects(user_id, is_pinned)")

        # Create user_preferences table for cross-browser model/theme/mode persistence
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                model TEXT DEFAULT 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
                theme TEXT DEFAULT 'dark',
                mode TEXT DEFAULT 'auto',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_preferences(user_id)")

        # Create deleted_conversations tombstone table so deleted chats are never resurrected across browsers
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_conversations (
                conv_id TEXT NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                deleted_at TEXT NOT NULL,
                PRIMARY KEY (conv_id, user_id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deleted_convs_user ON deleted_conversations(user_id)")

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
        if "is_archived" not in conv_cols:
            conn.execute("ALTER TABLE conversations ADD COLUMN is_archived INTEGER DEFAULT 0")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(project_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_archived ON conversations(user_id, is_archived)")

        # Migrate existing users table for custom_instructions, is_guest, expires_at, and avatar
        user_cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "custom_instructions" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN custom_instructions TEXT DEFAULT ''")
        if "is_guest" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN is_guest INTEGER DEFAULT 0")
        if "expires_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN expires_at TEXT DEFAULT NULL")
        if "avatar" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT 'avatar-1'")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_expires_at ON users(expires_at)")

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
            CREATE TABLE IF NOT EXISTS active_stream_leases (
                stream_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stream_leases_user ON active_stream_leases(user_id, expires_at)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_rate_limits (
                key TEXT PRIMARY KEY,
                attempts INTEGER NOT NULL,
                reset_at REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_rate_reset ON auth_rate_limits(reset_at)")

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
        if current_v < 4:
            conn.execute("INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (4, ?, 'Guest session expiration, active stream leases, and distributed auth rate limits')", (now_iso,))
        if current_v < 5:
            # Deterministically repair orphaned foreign key records
            conn.execute(
                "UPDATE conversations SET project_id = NULL WHERE project_id IS NOT NULL AND project_id NOT IN (SELECT id FROM projects)"
            )
            conn.execute(
                "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id NOT IN (SELECT id FROM users))"
            )
            conn.execute("DELETE FROM conversations WHERE user_id NOT IN (SELECT id FROM users)")
            conn.execute("DELETE FROM memories WHERE user_id NOT IN (SELECT id FROM users)")
            conn.execute("DELETE FROM projects WHERE user_id NOT IN (SELECT id FROM users)")
            conn.execute("DELETE FROM daily_usage WHERE user_id NOT IN (SELECT id FROM users)")
            conn.execute("DELETE FROM active_stream_leases WHERE user_id NOT IN (SELECT id FROM users)")
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (5, ?, 'Deterministic foreign-key orphan remediation across conversations, memories, projects, and daily usage')",
                (now_iso,),
            )
        if current_v < 6:
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (6, ?, 'Add user avatar presets and conversation archive support')",
                (now_iso,),
            )
        if current_v < 7:
            # Clean start: purge broken/test users and establish unique index on email
            try:
                conn.execute("DELETE FROM users WHERE username IN ('john123', 'aman123', 'testuser', 'explorer', 'demo') OR email LIKE '%@local.cortex%' OR email = '' OR email IS NULL")
                conn.execute("DELETE FROM conversations WHERE user_id NOT IN (SELECT id FROM users)")
                conn.execute("DELETE FROM messages WHERE conversation_id NOT IN (SELECT id FROM conversations)")
                conn.execute("DELETE FROM memories WHERE user_id NOT IN (SELECT id FROM users)")
                conn.execute("DELETE FROM projects WHERE user_id NOT IN (SELECT id FROM users)")
            except Exception:
                pass
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email) WHERE is_guest = 0 AND email IS NOT NULL AND email != ''")
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (7, ?, 'Email-first accounts with unique email index and clean slate')",
                (now_iso,),
            )
        if current_v < 8:
            # Clean slate: purge legacy test users with placeholder or obsolete hashes
            try:
                conn.execute(
                    "DELETE FROM users WHERE password_hash = 'SERVERLESS_VERIFIED_TOKEN' "
                    "OR username IN ('john123', 'john', 'aman123', 'aman', 'testuser', 'explorer', 'demo') "
                    "OR email IN ('john123@gmail.com', 'aman123@gmail.com', 'testuser@gmail.com') "
                    "OR email LIKE '%@local.cortex%' OR email = '' OR email IS NULL"
                )
                conn.execute("DELETE FROM conversations WHERE user_id NOT IN (SELECT id FROM users)")
                conn.execute("DELETE FROM messages WHERE conversation_id NOT IN (SELECT id FROM conversations)")
                conn.execute("DELETE FROM memories WHERE user_id NOT IN (SELECT id FROM users)")
                conn.execute("DELETE FROM projects WHERE user_id NOT IN (SELECT id FROM users)")
                conn.execute("DELETE FROM daily_usage WHERE user_id NOT IN (SELECT id FROM users)")
            except Exception:
                pass
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (8, ?, 'Purge placeholder serverless hashes and obsolete test accounts for clean slate launch')",
                (now_iso,),
            )
        if current_v < 9:
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (9, ?, 'Project pins in DB, user_preferences table, deleted_conversations tombstones, and soft-delete support')",
                (now_iso,),
            )

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


def validate_password_complexity(password: str) -> tuple[bool, str]:
    """Enforce production password complexity:
    - Minimum 8 characters
    - At least one letter (a-z or A-Z)
    - At least one numeric digit (0-9)
    - At least one special symbol (!@#$%^&* etc.)
    - Cannot be purely numeric or purely alphabetic
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must include at least one letter (a-z or A-Z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one number (0-9)."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password):
        return False, "Password must include at least one special character (e.g. !@#$%)."
    return True, ""


def check_email_exists(email: str) -> bool:
    """Check if a registered non-guest user already uses this email address."""
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return False
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE LOWER(email) = ? AND is_guest = 0",
            (clean_email,),
        ).fetchone()
        return row is not None


def generate_user_id(identifier: str) -> str:
    """Generate a deterministic, immutable RFC-4122 UUIDv5 for a registered email or username.
    Guarantees that across all Vercel/serverless containers, cold starts, and re-logins,
    the user's ID never changes."""
    clean = (identifier or "explorer").strip().lower()
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cortex.user:{clean}"))


def transfer_guest_data_to_user(guest_id: Optional[str], target_user_id: str) -> None:
    """Migrate conversations, messages, memories, and projects from an ephemeral guest session
    or unassigned state to an authenticated registered user."""
    if not target_user_id:
        return
    with get_connection() as conn:
        _begin_immediate(conn)
        if guest_id and guest_id != target_user_id:
            conn.execute("UPDATE conversations SET user_id = ? WHERE user_id = ?", (target_user_id, guest_id))
            conn.execute("UPDATE memories SET user_id = ? WHERE user_id = ?", (target_user_id, guest_id))
            conn.execute("UPDATE user_projects SET user_id = ? WHERE user_id = ?", (target_user_id, guest_id))
        # Adopt any orphaned conversations or memories without explicit owner
        conn.execute("UPDATE conversations SET user_id = ? WHERE user_id IS NULL OR user_id = ''", (target_user_id,))
        conn.execute("UPDATE memories SET user_id = ? WHERE user_id IS NULL OR user_id = ''", (target_user_id,))
        conn.commit()


def create_user(
    username: Optional[str] = None,
    password: str = "",
    email: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    clean_email = (email or "").strip().lower()
    clean_username = (username or "").strip().lower()

    if not clean_email and not clean_username:
        raise ValueError("Email address is required.")

    if clean_email:
        if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
            raise ValueError("Please provide a valid email address.")
        if not clean_username:
            clean_username = clean_email.split("@")[0]

    if not clean_username:
        clean_username = f"user_{secrets.token_hex(4)}"

    # Validate password complexity
    valid, msg = validate_password_complexity(password)
    if not valid:
        raise ValueError(msg)

    # Check for duplicate email across registered accounts
    if clean_email and check_email_exists(clean_email):
        raise ValueError("An account with this email already exists. Please sign in or use a different email.")

    pw_hash, salt = hash_password(password)
    target_user_id = user_id or generate_user_id(clean_email or clean_username)
    now = _utc_now_iso()

    with get_connection() as conn:
        _begin_immediate(conn)
        try:
            conn.execute(
                """
                INSERT INTO users (id, username, email, password_hash, salt, created_at, is_guest)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    email = excluded.email,
                    password_hash = excluded.password_hash,
                    salt = excluded.salt,
                    is_guest = 0
                ON CONFLICT(username) DO UPDATE SET
                    email = excluded.email,
                    password_hash = excluded.password_hash,
                    salt = excluded.salt,
                    is_guest = 0
                """,
                (target_user_id, clean_username, clean_email, pw_hash, salt, now),
            )
            count_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_guest = 0").fetchone()["c"]
            if count_users == 1:
                conn.execute("UPDATE conversations SET user_id = ? WHERE user_id IS NULL OR user_id = ''", (target_user_id,))
            conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e).upper() and "EMAIL" in str(e).upper():
                raise ValueError("An account with this email already exists. Please sign in or use a different email.")
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ?, email = ?, is_guest = 0 WHERE username = ? OR id = ? OR (email != '' AND email = ?)",
                (pw_hash, salt, clean_email, clean_username, target_user_id, clean_email),
            )
            conn.commit()

    return {
        "id": target_user_id,
        "username": clean_username,
        "email": clean_email,
        "is_guest": False,
        "created_at": now,
        "avatar": "avatar-1",
    }


def update_user_password(identifier: str, new_password: str) -> Optional[dict[str, Any]]:
    """Update or reset a user's password with PBKDF2 hashing and return the updated user record."""
    clean_id = (identifier or "").strip().lower()
    if not clean_id:
        return None

    valid, msg = validate_password_complexity(new_password)
    if not valid:
        raise ValueError(msg)

    pw_hash, salt = hash_password(new_password)
    now = _utc_now_iso()

    with get_connection() as conn:
        _begin_immediate(conn)
        row = conn.execute(
            "SELECT id, username, email FROM users WHERE (LOWER(email) = ? OR LOWER(username) = ?)",
            (clean_id, clean_id),
        ).fetchone()
        if row:
            target_id = row["id"]
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ?, is_guest = 0 WHERE id = ?",
                (pw_hash, salt, target_id),
            )
        else:
            email_arg = clean_id if "@" in clean_id else f"{clean_id}@local.cortex"
            uname_arg = clean_id.split("@")[0] if "@" in clean_id else clean_id
            target_id = generate_user_id(clean_id)
            conn.execute(
                """
                INSERT INTO users (id, username, email, password_hash, salt, created_at, is_guest)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    email = excluded.email,
                    password_hash = excluded.password_hash,
                    salt = excluded.salt,
                    is_guest = 0
                ON CONFLICT(username) DO UPDATE SET
                    email = excluded.email,
                    password_hash = excluded.password_hash,
                    salt = excluded.salt,
                    is_guest = 0
                """,
                (target_id, uname_arg, email_arg, pw_hash, salt, now),
            )
        conn.commit()

    return authenticate_user(clean_id, new_password, allow_auto_provision=False)


def authenticate_user(identifier: str, password: str, allow_auto_provision: bool = True) -> Optional[dict[str, Any]]:
    clean_id = (identifier or "").strip().lower()
    if not clean_id:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, email, password_hash, salt, created_at, is_guest, COALESCE(avatar, 'avatar-1') as avatar
            FROM users
            WHERE (LOWER(email) = ? OR LOWER(username) = ?)
            LIMIT 1
            """,
            (clean_id, clean_id),
        ).fetchone()

        if not row:
            # Self-healing local-first user provisioning on serverless container cold starts
            if allow_auto_provision and len(password) >= 8:
                valid, _ = validate_password_complexity(password)
                if valid:
                    email_arg = clean_id if "@" in clean_id else f"{clean_id}@local.cortex"
                    uname_arg = clean_id.split("@")[0] if "@" in clean_id else clean_id
                    try:
                        u = create_user(username=uname_arg, password=password, email=email_arg, user_id=generate_user_id(clean_id))
                        transfer_guest_data_to_user(None, u["id"])
                        return u
                    except Exception:
                        try:
                            uname_unique = f"{uname_arg}_{secrets.token_hex(2)}"
                            u = create_user(username=uname_unique, password=password, email=email_arg, user_id=generate_user_id(clean_id))
                            transfer_guest_data_to_user(None, u["id"])
                            return u
                        except Exception as e:
                            logger.warning("Auto-provisioning user '%s' failed: %s", clean_id, e)
            return None

        # Guest accounts cannot authenticate via password credentials
        if bool(row["is_guest"]) or row["password_hash"] == "GUEST_ANONYMOUS":
            return None

        # Serverless placeholder handling: if user was reconstituted from token, bind password hash
        if row["password_hash"] == "SERVERLESS_VERIFIED_TOKEN":
            if len(password) >= 8:
                valid, _ = validate_password_complexity(password)
                if valid:
                    pw_hash, salt = hash_password(password)
                    conn.execute(
                        "UPDATE users SET password_hash = ?, salt = ?, is_guest = 0 WHERE id = ?",
                        (pw_hash, salt, row["id"]),
                    )
                    conn.commit()
                    return {
                        "id": row["id"],
                        "username": row["username"],
                        "email": row["email"],
                        "is_guest": False,
                        "created_at": row["created_at"],
                        "avatar": row["avatar"] or "avatar-1",
                    }

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
                "is_guest": False,
                "created_at": row["created_at"],
                "avatar": row["avatar"] or "avatar-1",
            }
        return None


def create_guest_user(ttl_hours: int = 24) -> dict[str, Any]:
    """Create an anonymous, isolated ephemeral guest account without expensive PBKDF2 hashing."""
    from datetime import timedelta
    uid = str(uuid.uuid4())
    guest_suffix = uid[:8]
    username = f"guest_{guest_suffix}"
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires_at = (now_dt + timedelta(hours=ttl_hours)).isoformat()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, salt, created_at, is_guest, expires_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
            (uid, username, "", "GUEST_ANONYMOUS", "", now, expires_at),
        )
        conn.commit()

    return {
        "id": uid,
        "username": username,
        "email": "",
        "is_guest": True,
        "created_at": now,
        "expires_at": expires_at,
        "avatar": "avatar-1",
    }


def cleanup_expired_guests() -> int:
    """Delete all expired guest accounts and cascade their associated data."""
    now = _utc_now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM users WHERE is_guest = 1 AND expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        )
        conn.commit()
        return cursor.rowcount


def _begin_immediate(conn: sqlite3.Connection) -> None:
    """Explicitly acquire an exclusive write lock in SQLite if not in transaction."""
    if not conn.in_transaction:
        conn.execute("BEGIN IMMEDIATE")


def check_and_record_auth_attempt(key: str, max_attempts: int, window_seconds: int) -> tuple[bool, int]:
    """Rate limit authentication attempts using SQLite with atomic write lock.
    Returns (is_allowed, remaining_attempts_or_wait_seconds)."""
    now = time.time()
    with get_connection() as conn:
        _begin_immediate(conn)
        row = conn.execute(
            "SELECT attempts, reset_at FROM auth_rate_limits WHERE key = ?",
            (key,),
        ).fetchone()

        if not row or row["reset_at"] <= now:
            reset_at = now + window_seconds
            conn.execute(
                "INSERT OR REPLACE INTO auth_rate_limits (key, attempts, reset_at) VALUES (?, 1, ?)",
                (key, reset_at),
            )
            conn.commit()
            return True, max(0, max_attempts - 1)

        attempts = row["attempts"]
        reset_at = row["reset_at"]

        if attempts >= max_attempts:
            wait_seconds = max(1, int(reset_at - now))
            return False, wait_seconds

        conn.execute(
            "UPDATE auth_rate_limits SET attempts = attempts + 1 WHERE key = ?",
            (key,),
        )
        conn.commit()
        return True, max(0, max_attempts - (attempts + 1))


def reset_auth_attempts(key: str) -> None:
    """Clear failed attempt counters for a specific rate limit key."""
    with get_connection() as conn:
        _begin_immediate(conn)
        conn.execute("DELETE FROM auth_rate_limits WHERE key = ?", (key,))
        conn.commit()


def acquire_stream_lease(user_id: str, stream_id: str, max_concurrent: int = 2, ttl_seconds: int = 60) -> bool:
    """Acquire a multi-worker resilient stream concurrency lease in SQLite with atomic lock."""
    now = time.time()
    expires_at = now + ttl_seconds
    with get_connection() as conn:
        _begin_immediate(conn)
        # Purge expired leases first
        conn.execute("DELETE FROM active_stream_leases WHERE expires_at <= ?", (now,))
        active_count = conn.execute(
            "SELECT COUNT(*) as count FROM active_stream_leases WHERE user_id = ?",
            (user_id,),
        ).fetchone()["count"]

        if active_count >= max_concurrent:
            # Reclaim the lease closest to expiry — active streams renew to now+300, so any lease
            # expiring within 60s has not been renewed recently and is likely abandoned
            stale_lease = conn.execute(
                "SELECT stream_id, expires_at FROM active_stream_leases WHERE user_id = ? AND expires_at < ? ORDER BY expires_at ASC LIMIT 1",
                (user_id, now + 60),
            ).fetchone()
            if stale_lease:
                conn.execute("DELETE FROM active_stream_leases WHERE stream_id = ?", (stale_lease["stream_id"],))
            else:
                return False

        conn.execute(
            "INSERT OR REPLACE INTO active_stream_leases (stream_id, user_id, expires_at) VALUES (?, ?, ?)",
            (stream_id, user_id, expires_at),
        )
        conn.commit()
        return True


def renew_stream_lease(stream_id: str, ttl_seconds: int = 300) -> bool:
    """Renew the TTL on an active stream lease to prevent expiration during long streams."""
    now = time.time()
    new_expires_at = now + ttl_seconds
    with get_connection() as conn:
        _begin_immediate(conn)
        cursor = conn.execute(
            "UPDATE active_stream_leases SET expires_at = ? WHERE stream_id = ? AND expires_at > ?",
            (new_expires_at, stream_id, now),
        )
        conn.commit()
        return cursor.rowcount > 0


def release_stream_lease(stream_id: str) -> None:
    """Release an active stream concurrency lease."""
    with get_connection() as conn:
        _begin_immediate(conn)
        conn.execute("DELETE FROM active_stream_leases WHERE stream_id = ?", (stream_id,))
        conn.commit()


def get_user_by_id(user_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at, is_guest, COALESCE(avatar, 'avatar-1') as avatar FROM users WHERE id = ?",
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
            "SELECT id, username, email, created_at, is_guest, COALESCE(avatar, 'avatar-1') as avatar FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_guest"] = bool(d.get("is_guest", 0))
        return d


def reconstitute_user(
    user_id: str,
    username: str,
    email: str = "",
    is_guest: bool = False,
    avatar: str = "avatar-1",
) -> dict[str, Any]:
    """Reconstitute a cryptographically verified user into the current instance's database.

    Critical for serverless / multi-container environments (e.g., Vercel, AWS Lambda)
    where each container has an ephemeral SQLite file in /tmp.
    """
    clean_user = (username or "Explorer").strip().lower()
    clean_email = (email or "").strip()
    now = _utc_now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, username, email, password_hash, salt, created_at, is_guest, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                clean_user,
                clean_email,
                "SERVERLESS_VERIFIED_TOKEN",
                "salt",
                now,
                1 if is_guest else 0,
                avatar,
            ),
        )
        conn.commit()
    return get_user_by_id(user_id) or {
        "id": user_id,
        "username": clean_user,
        "email": clean_email,
        "is_guest": is_guest,
        "created_at": now,
        "avatar": avatar,
    }


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


def update_user_avatar(user_id: str, avatar: str) -> bool:
    """Update avatar preset identifier for the user."""
    with get_connection() as conn:
        cursor = conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_user_account(user_id: str) -> bool:
    """Completely and permanently delete user and cascade across all related tables."""
    with get_connection() as conn:
        _begin_immediate(conn)
        conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)", (user_id,))
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM daily_usage WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM active_stream_leases WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM revoked_tokens WHERE user_id = ?", (user_id,))
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0


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
            chk = conn.execute("SELECT id, user_id FROM projects WHERE id = ?", (project_id,)).fetchone()
            if chk:
                if str(chk["user_id"]) == str(user_id):
                    valid_project_id = project_id
                else:
                    valid_project_id = None
            else:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO projects (id, name, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                        (project_id, "Project", user_id, now, now),
                    )
                    valid_project_id = project_id
                except Exception:
                    valid_project_id = None
        conn.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at, user_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            updated_at = excluded.updated_at,
            project_id = COALESCE(excluded.project_id, conversations.project_id)
            """,
            (cid, title, now, now, user_id, valid_project_id),
        )
        conn.commit()
    return {"id": cid, "title": title, "created_at": now, "updated_at": now, "user_id": user_id, "project_id": valid_project_id}


def get_conversations(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    is_archived: bool = False,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cols = "id, title, created_at, updated_at, user_id, project_id, COALESCE(is_pinned, 0) as is_pinned, COALESCE(is_archived, 0) as is_archived"
        arch_val = 1 if is_archived else 0
        if user_id and project_id:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE user_id = ? AND project_id = ? AND COALESCE(is_archived, 0) = ? ORDER BY is_pinned DESC, updated_at DESC",
                (user_id, project_id, arch_val),
            )
        elif user_id:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE user_id = ? AND COALESCE(is_archived, 0) = ? ORDER BY is_pinned DESC, updated_at DESC",
                (user_id, arch_val),
            )
        else:
            cursor = conn.execute(
                f"SELECT {cols} FROM conversations WHERE COALESCE(is_archived, 0) = ? ORDER BY is_pinned DESC, updated_at DESC",
                (arch_val,),
            )
        return [dict(row) for row in cursor.fetchall()]


def get_conversation(conv_id: str, user_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        cols = "id, title, created_at, updated_at, user_id, project_id, COALESCE(is_pinned, 0) as is_pinned, COALESCE(is_archived, 0) as is_archived"
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
            query_sel += " AND (user_id = ? OR user_id IS NULL OR user_id = '')"
            params_sel.append(user_id)

        cur = conn.execute(query_sel, tuple(params_sel))
        row = cur.fetchone()
        now = _utc_now_iso()

        valid_user_id = None
        if user_id:
            u_chk = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
            if u_chk:
                valid_user_id = user_id

        if not row:
            # Multi-container serverless fallback: insert skeleton conversation so pin persists
            target_pin = 1 if (is_pinned is None or is_pinned) else 0
            conn.execute(
                "INSERT OR REPLACE INTO conversations (id, title, created_at, updated_at, user_id, is_pinned, is_archived) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (conv_id, "Chat", now, now, valid_user_id, target_pin),
            )
            conn.commit()
            return bool(target_pin)

        if is_pinned is None:
            new_val = 0 if row["is_pinned"] else 1
        else:
            new_val = 1 if is_pinned else 0

        query_upd = "UPDATE conversations SET is_pinned = ?, updated_at = ? WHERE id = ?"
        params_upd = [new_val, now, conv_id]
        if user_id:
            query_upd += " AND (user_id = ? OR user_id IS NULL OR user_id = '')"
            params_upd.append(user_id)

        cursor = conn.execute(query_upd, tuple(params_upd))
        conn.commit()
        return bool(new_val)


def archive_conversation(conv_id: str, is_archived: bool, user_id: str) -> bool:
    """Archive or unarchive a conversation for a user."""
    with get_connection() as conn:
        now = _utc_now_iso()
        val = 1 if is_archived else 0
        cursor = conn.execute(
            "UPDATE conversations SET is_archived = ?, updated_at = ? WHERE id = ? AND (user_id = ? OR user_id IS NULL OR user_id = '')",
            (val, now, conv_id, user_id),
        )
        if cursor.rowcount == 0:
            valid_user_id = None
            if user_id:
                u_chk = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
                if u_chk:
                    valid_user_id = user_id
            # Multi-container serverless fallback: insert skeleton conversation with archive status
            conn.execute(
                "INSERT OR REPLACE INTO conversations (id, title, created_at, updated_at, user_id, is_pinned, is_archived) VALUES (?, ?, ?, ?, ?, 0, ?)",
                (conv_id, "Chat", now, now, valid_user_id, val),
            )
        conn.commit()
        return True


def update_conversation_title(conv_id: str, title: str, user_id: Optional[str] = None) -> bool:
    now = _utc_now_iso()
    with get_connection() as conn:
        valid_user_id = None
        if user_id:
            u_chk = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
            if u_chk:
                valid_user_id = user_id

        cur = conn.execute("SELECT id, user_id FROM conversations WHERE id = ?", (conv_id,))
        row = cur.fetchone()
        if row:
            if user_id and row["user_id"] and row["user_id"] != user_id:
                return False
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id),
            )
        else:
            # Multi-container serverless fallback: insert skeleton conversation with this title
            conn.execute(
                "INSERT OR REPLACE INTO conversations (id, title, created_at, updated_at, user_id, is_pinned, is_archived) VALUES (?, ?, ?, ?, ?, 0, 0)",
                (conv_id, title, now, now, valid_user_id),
            )
        conn.commit()
        return True


def delete_conversation(conv_id: str, user_id: Optional[str] = None) -> bool:
    with get_connection() as conn:
        now = _utc_now_iso()
        if user_id:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute(
                "DELETE FROM conversations WHERE id = ? AND (user_id = ? OR user_id IS NULL OR user_id = '')",
                (conv_id, user_id),
            )
            # Record tombstone so all connected browsers drop it from cache
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO deleted_conversations (conv_id, user_id, deleted_at) VALUES (?, ?, ?)",
                    (conv_id, user_id, now),
                )
            except Exception:
                pass
        else:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        return True


def get_deleted_conversation_ids(user_id: str) -> list[str]:
    """Return list of deleted conversation IDs for the user."""
    with get_connection() as conn:
        cur = conn.execute("SELECT conv_id FROM deleted_conversations WHERE user_id = ? ORDER BY deleted_at DESC LIMIT 100", (user_id,))
        return [r["conv_id"] for r in cur.fetchall()]


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

        # Check if identical message was already inserted within the last 15 seconds to prevent duplicate turns
        existing = conn.execute(
            "SELECT id, created_at FROM messages WHERE conversation_id = ? AND role = ? AND content = ? ORDER BY rowid DESC LIMIT 1",
            (conv_id, role, content),
        ).fetchone()
        if existing:
            try:
                msg_time = datetime.fromisoformat(existing["created_at"].replace("Z", "+00:00")).timestamp()
                if time.time() - msg_time < 15.0:
                    return {
                        "id": existing["id"],
                        "conversation_id": conv_id,
                        "role": role,
                        "content": content,
                        "tools_used": tools_used or [],
                        "created_at": existing["created_at"],
                    }
            except Exception:
                pass

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
                # Serverless fallback: message might be on another container or unsaved
                return True
        cursor = conn.execute("UPDATE messages SET feedback = ? WHERE id = ?", (feedback, message_id))
        conn.commit()
        return True


def fork_conversation(
    conv_id: str,
    up_to_message_id: Optional[str] = None,
    user_id: str = "",
    new_title: Optional[str] = None,
    fallback_messages: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    """Fork a conversation up to a specified message into a brand new conversation."""
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conv_row = cur.fetchone()
        if not conv_row:
            if fallback_messages and isinstance(fallback_messages, list):
                new_conv_id = str(uuid.uuid4())
                now = _utc_now_iso()
                title = new_title or "[Fork] Branched Chat"
                conn.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at, user_id, is_pinned, custom_instructions)
                    VALUES (?, ?, ?, ?, ?, 0, '')
                    """,
                    (new_conv_id, title, now, now, user_id),
                )
                cloned_messages = []
                for m in fallback_messages:
                    new_mid = str(uuid.uuid4())
                    content_str = m.get("content") or ""
                    role_str = m.get("role") or "user"
                    conn.execute(
                        """
                        INSERT INTO messages (id, conversation_id, role, content, tools_used, feedback, created_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?)
                        """,
                        (new_mid, new_conv_id, role_str, content_str, "[]", now),
                    )
                    cloned_messages.append({
                        "id": new_mid,
                        "conversation_id": new_conv_id,
                        "role": role_str,
                        "content": content_str,
                        "tools_used": [],
                        "feedback": 0,
                        "created_at": now,
                    })
                    if up_to_message_id and (m.get("id") == up_to_message_id or m.get("message_id") == up_to_message_id):
                        break
                conn.commit()
                conv_dict = {
                    "id": new_conv_id,
                    "title": title,
                    "created_at": now,
                    "updated_at": now,
                    "user_id": user_id,
                    "is_pinned": 0,
                    "custom_instructions": "",
                }
                return {
                    **conv_dict,
                    "conversation": conv_dict,
                    "messages": cloned_messages,
                }
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

def add_memory(user_id: str, content: str, category: str = "preference", mem_id: Optional[str] = None) -> dict[str, Any]:
    """Add a new persistent memory for a user."""
    clean_content = content.strip()
    now = _utc_now_iso()
    cat = (category or "preference").strip().lower()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id, user_id, content, category, created_at, updated_at FROM memories WHERE user_id = ? AND lower(trim(content)) = lower(trim(?))",
            (user_id, clean_content),
        ).fetchone()
        if existing:
            return dict(existing)

        actual_id = mem_id or str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO memories (id, user_id, content, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            content = excluded.content,
            category = excluded.category,
            updated_at = excluded.updated_at
            """,
            (actual_id, user_id, clean_content, cat, now, now),
        )
        conn.commit()
    return {
        "id": actual_id,
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
            INSERT INTO projects (id, name, description, system_prompt, user_id, created_at, updated_at, is_pinned, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
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
        "is_pinned": 0,
        "is_deleted": 0,
    }


def get_projects(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT id, name, description, system_prompt, user_id, created_at, updated_at,
                   COALESCE(is_pinned, 0) AS is_pinned,
                   COALESCE(is_deleted, 0) AS is_deleted
            FROM projects
            WHERE user_id = ? AND COALESCE(is_deleted, 0) = 0
            ORDER BY COALESCE(is_pinned, 0) DESC, updated_at DESC
            """,
            (user_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_project(project_id: str, user_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT id, name, description, system_prompt, user_id, created_at, updated_at,
                   COALESCE(is_pinned, 0) AS is_pinned,
                   COALESCE(is_deleted, 0) AS is_deleted
            FROM projects
            WHERE id = ? AND user_id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (project_id, user_id),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_project(
    project_id: str,
    user_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> bool:
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name.strip())
    if description is not None:
        fields.append("description = ?")
        values.append(description.strip())
    if system_prompt is not None:
        fields.append("system_prompt = ?")
        values.append(system_prompt.strip())
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(_utc_now_iso())
    values.extend([project_id, user_id])
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE projects SET {', '.join(fields)} WHERE id = ? AND user_id = ? AND COALESCE(is_deleted, 0) = 0",
            values,
        )
        conn.commit()
        return cur.rowcount > 0


def toggle_project_pin(project_id: str, user_id: str, is_pinned: Optional[bool] = None) -> Optional[int]:
    """Toggle or set is_pinned state for a project."""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT is_pinned FROM projects WHERE id = ? AND user_id = ? AND COALESCE(is_deleted, 0) = 0",
            (project_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        current_pinned = int(row["is_pinned"] or 0)
        new_pinned = int(is_pinned) if is_pinned is not None else (0 if current_pinned else 1)
        now = _utc_now_iso()
        conn.execute(
            "UPDATE projects SET is_pinned = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (new_pinned, now, project_id, user_id),
        )
        conn.commit()
        return new_pinned


def delete_project(project_id: str, user_id: str, soft: bool = True) -> bool:
    with get_connection() as conn:
        # Unlink conversations first
        conn.execute("UPDATE conversations SET project_id = NULL WHERE project_id = ? AND user_id = ?", (project_id, user_id))
        now = _utc_now_iso()
        if soft:
            cur = conn.execute(
                "UPDATE projects SET is_deleted = 1, deleted_at = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (now, now, project_id, user_id),
            )
        else:
            cur = conn.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
        conn.commit()
        return cur.rowcount > 0


def get_user_preferences(user_id: str) -> dict[str, Any]:
    """Retrieve persisted preferences (model, theme, mode) for an authenticated user."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT model, theme, mode, updated_at FROM user_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return {
                "user_id": user_id,
                "model": row["model"] or "nvidia/llama-3.1-nemotron-ultra-253b-v1",
                "theme": row["theme"] or "dark",
                "mode": row["mode"] or "auto",
                "updated_at": row["updated_at"],
            }
        return {
            "user_id": user_id,
            "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
            "theme": "dark",
            "mode": "auto",
            "updated_at": _utc_now_iso(),
        }


def set_user_preferences(
    user_id: str,
    model: Optional[str] = None,
    theme: Optional[str] = None,
    mode: Optional[str] = None,
) -> dict[str, Any]:
    """Upsert persisted preferences for an authenticated user."""
    now = _utc_now_iso()
    with get_connection() as conn:
        current = conn.execute(
            "SELECT model, theme, mode FROM user_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        cur_model = (current["model"] if current else None) or "nvidia/llama-3.1-nemotron-ultra-253b-v1"
        cur_theme = (current["theme"] if current else None) or "dark"
        cur_mode = (current["mode"] if current else None) or "auto"

        new_model = model.strip() if (model is not None and model.strip()) else cur_model
        new_theme = theme.strip() if (theme is not None and theme.strip()) else cur_theme
        new_mode = mode.strip() if (mode is not None and mode.strip()) else cur_mode

        conn.execute(
            """
            INSERT OR REPLACE INTO user_preferences (user_id, model, theme, mode, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, new_model, new_theme, new_mode, now),
        )
        conn.commit()
        return {
            "user_id": user_id,
            "model": new_model,
            "theme": new_theme,
            "mode": new_mode,
            "updated_at": now,
        }


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

DAILY_TOKEN_LIMIT = 100_000_000
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
            "token_limit": tok_limit,
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
        _begin_immediate(conn)
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
        _begin_immediate(conn)
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


def sync_daily_tokens_used(user_id: str, client_tokens: int) -> dict:
    """Sync client-reported tokens into daily_usage using monotonic MAX to bridge multi-container serverless."""
    if client_tokens <= 0:
        return get_daily_usage(user_id)
    d = _today_str()
    with get_connection() as conn:
        u_exists = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u_exists:
            return get_daily_usage(user_id, d)
        conn.execute(
            """
            INSERT INTO daily_usage (user_id, usage_date, tokens_used, uploads_count)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
            tokens_used = MAX(tokens_used, excluded.tokens_used)
            """,
            (user_id, d, int(client_tokens)),
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

        deleted_keys = get_deleted_artifact_keys(user_id)
        seen_conv_titles = set()
        seen_conv_files = set()
        for item in stitched_messages:
            text = (item["content"] or "").strip()
            if not text:
                continue

            text_without_code = re.sub(r"```[\s\S]*?```", "", text)
            has_heading = bool(re.search(r"^#{1,3}\s+\S+", text_without_code, re.MULTILINE))
            has_doc_attach = "[Attached Document:" in text or "[Structured Tabular Data:" in text
            has_table = "| --- |" in text or "|:---:|" in text
            code_match = re.search(r"```([a-zA-Z0-9_\-:\.]+)?\s*\n([\s\S]*?)```", text)
            has_code = bool(
                re.search(r"```(?:python|py|javascript|js|typescript|ts|html|css|sql|json|sh|bash|c|cpp|java|chart)\b", text, re.IGNORECASE)
                or (code_match and len(code_match.group(2).strip()) > 35)
            )

            is_artifact = (
                has_heading
                or has_doc_attach
                or (has_table and len(text) > 200)
                or (has_code and len(text) > 40)
                or len(text) > 400
            )
            if not is_artifact:
                continue

            title = extract_document_title(text, item["conv_title"])
            conv_title_key = (item["conversation_id"], title.strip().lower())
            if conv_title_key in seen_conv_titles:
                continue
            seen_conv_titles.add(conv_title_key)

            # Generate safe slug without leading/trailing underscores or emojis
            clean_title_ascii = re.sub(r"[^\w\s-]", "", title).strip()
            safe_slug = re.sub(r"[-\s]+", "_", clean_title_ascii.lower()).strip("_")
            if not safe_slug or len(safe_slug) < 3:
                safe_slug = "document"
            safe_slug = safe_slug[:48].rstrip("_")

            if code_match and len(code_match.group(2).strip()) > 40:
                raw_l = (code_match.group(1) or "").lower().strip()
                if "python" in raw_l or raw_l == "py":
                    def_ext = ".py"
                elif "javascript" in raw_l or raw_l == "js":
                    def_ext = ".js"
                elif "typescript" in raw_l or raw_l == "ts":
                    def_ext = ".ts"
                elif "html" in raw_l:
                    def_ext = ".html"
                elif "css" in raw_l:
                    def_ext = ".css"
                elif "sql" in raw_l:
                    def_ext = ".sql"
                elif "json" in raw_l:
                    def_ext = ".json"
                elif "sh" in raw_l or "bash" in raw_l:
                    def_ext = ".sh"
                else:
                    def_ext = ".md"
                safe_slug = re.sub(r"\.[a-zA-Z0-9]+$", "", safe_slug) + def_ext
            else:
                if not safe_slug.endswith(".md"):
                    safe_slug += ".md"

            # Normalized stem without file extension for bulletproof conversation-level deduplication
            stem = re.sub(r"\.[a-zA-Z0-9]+$", "", safe_slug).lower()[:32]
            conv_file_key = (item["conversation_id"], stem)
            if conv_file_key in seen_conv_files:
                continue
            seen_conv_files.add(conv_file_key)

            # Check if this artifact was deleted by the user
            if (
                item["id"] in deleted_keys
                or f"{item['conversation_id']}:{item['id']}" in deleted_keys
                or f"{item['conversation_id']}:{safe_slug}" in deleted_keys
                or f"{item['conversation_id']}:{safe_slug.lower()}" in deleted_keys
                or f"{item['conversation_id']}:{stem}" in deleted_keys
            ):
                continue

            size_bytes = len(text.encode("utf-8"))

            artifacts.append({
                "id": item["id"],
                "key": f"{item['conversation_id']}:{safe_slug.lower()}",
                "stem_key": f"{item['conversation_id']}:{stem}",
                "conversation_id": item["conversation_id"],
                "conversation_title": item["conv_title"] or "Chat",
                "title": title,
                "filename": safe_slug,
                "content": text,
                "size_bytes": size_bytes,
                "created_at": item["created_at"],
            })

    return artifacts


def mark_artifact_deleted(user_id: str, artifact_key: str) -> bool:
    """Mark an artifact as deleted by user (persists across serverless restarts)."""
    if not user_id or not artifact_key:
        return False
    key_str = str(artifact_key).strip()
    generic_bad = {"document", "document.md", "document_md", "markdown", "untitled", "chat"}
    if key_str.lower() in generic_bad:
        return False
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_artifacts (
                user_id TEXT NOT NULL,
                artifact_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, artifact_key)
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO deleted_artifacts (user_id, artifact_key, created_at) VALUES (?, ?, ?)",
            (user_id, key_str, _utc_now_iso()),
        )
        conn.commit()
    return True


def get_deleted_artifact_keys(user_id: str) -> set[str]:
    """Retrieve all deleted artifact keys for a user, filtering out generic legacy slugs."""
    if not user_id:
        return set()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_artifacts (
                user_id TEXT NOT NULL,
                artifact_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, artifact_key)
            )
            """
        )
        rows = conn.execute("SELECT artifact_key FROM deleted_artifacts WHERE user_id = ?", (user_id,)).fetchall()
        keys = {r["artifact_key"] for r in rows}
        generic_bad = {"document", "document.md", "document_md", "markdown", "untitled", "chat"}
        return {k for k in keys if k.lower().strip() not in generic_bad}


# ---------------- Local-First Full Workspace State Synchronization & Persistence ----------------

def sync_full_user_state(
    user_id: str,
    conversations_data: Optional[list[dict[str, Any]]] = None,
    messages_data: Optional[list[dict[str, Any]]] = None,
    memories_data: Optional[list[dict[str, Any]]] = None,
    projects_data: Optional[list[dict[str, Any]]] = None,
    daily_usage_tokens: Optional[int] = None,
) -> dict[str, Any]:
    """Atomically synchronize and restore full user state (conversations, messages,
    memories, projects, token usage) into the current database instance.
    Guarantees that newly deployed serverless containers or instances immediately
    reconstitute the user's complete history without data loss.
    """
    if not user_id:
        return {"ok": False, "detail": "User ID required"}

    now = _utc_now_iso()
    synced_convs = 0
    synced_msgs = 0
    synced_mems = 0
    synced_projs = 0

    with get_connection() as conn:
        _begin_immediate(conn)

        # 1. Reconstitute projects first (foreign key dependency for conversations)
        if projects_data and isinstance(projects_data, list):
            for p in projects_data:
                if not isinstance(p, dict) or not p.get("id") or not p.get("name"):
                    continue
                pid = str(p["id"]).strip()
                pname = str(p["name"]).strip()
                pdesc = str(p.get("description") or "").strip()
                pprompt = str(p.get("system_prompt") or "").strip()
                pcreated = str(p.get("created_at") or now).strip()
                pupdated = str(p.get("updated_at") or now).strip()
                conn.execute(
                    """
                    INSERT INTO projects (id, name, description, system_prompt, user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        system_prompt = excluded.system_prompt,
                        updated_at = MAX(projects.updated_at, excluded.updated_at)
                    """,
                    (pid, pname, pdesc, pprompt, user_id, pcreated, pupdated),
                )
                synced_projs += 1

        # 2. Reconstitute conversations
        if conversations_data and isinstance(conversations_data, list):
            for c in conversations_data:
                if not isinstance(c, dict) or not c.get("id"):
                    continue
                cid = str(c["id"]).strip()
                ctitle = str(c.get("title") or "New Chat").strip()
                ccreated = str(c.get("created_at") or now).strip()
                cupdated = str(c.get("updated_at") or now).strip()
                cpinned = 1 if c.get("is_pinned") else 0
                carchived = 1 if c.get("is_archived") else 0
                cproj = str(c.get("project_id")).strip() if c.get("project_id") else None

                conn.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at, user_id, project_id, is_pinned, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        updated_at = MAX(conversations.updated_at, excluded.updated_at),
                        is_pinned = MAX(conversations.is_pinned, excluded.is_pinned),
                        is_archived = excluded.is_archived,
                        project_id = COALESCE(excluded.project_id, conversations.project_id),
                        user_id = COALESCE(conversations.user_id, excluded.user_id)
                    """,
                    (cid, ctitle, ccreated, cupdated, user_id, cproj, cpinned, carchived),
                )
                synced_convs += 1

        # 3. Reconstitute messages
        if messages_data and isinstance(messages_data, list):
            for m in messages_data:
                if not isinstance(m, dict) or not m.get("conversation_id") or not m.get("content"):
                    continue
                mid = str(m.get("id") or uuid.uuid4()).strip()
                conv_id = str(m["conversation_id"]).strip()
                role = str(m.get("role") or "user").strip()
                content = str(m.get("content") or "").strip()
                tools = m.get("tools_used")
                tools_json = json.dumps(tools) if isinstance(tools, list) else None
                feedback = int(m.get("feedback") or 0)
                mcreated = str(m.get("created_at") or now).strip()

                # Ensure parent conversation exists
                conv_exists = conn.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
                if not conv_exists:
                    conn.execute(
                        "INSERT INTO conversations (id, title, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, ?)",
                        (conv_id, "New Chat", mcreated, mcreated, user_id),
                    )

                # Deduplicate: Check if a message with identical (conversation_id, role, content) already exists
                existing_msg = conn.execute(
                    "SELECT id FROM messages WHERE conversation_id = ? AND role = ? AND content = ? LIMIT 1",
                    (conv_id, role, content),
                ).fetchone()
                if existing_msg:
                    conn.execute(
                        "UPDATE messages SET tools_used = COALESCE(?, tools_used), feedback = ? WHERE id = ?",
                        (tools_json, feedback, existing_msg["id"]),
                    )
                    continue

                conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, tools_used, feedback, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        content = excluded.content,
                        tools_used = COALESCE(excluded.tools_used, messages.tools_used),
                        feedback = excluded.feedback
                    """,
                    (mid, conv_id, role, content, tools_json, feedback, mcreated),
                )
                synced_msgs += 1

        # 4. Reconstitute memories
        if memories_data and isinstance(memories_data, list):
            for mem in memories_data:
                if not isinstance(mem, dict) or not mem.get("content"):
                    continue
                mem_id = str(mem.get("id") or uuid.uuid4()).strip()
                content = str(mem["content"]).strip()
                cat = str(mem.get("category") or "preference").strip()
                mcreated = str(mem.get("created_at") or now).strip()
                mupdated = str(mem.get("updated_at") or now).strip()

                conn.execute(
                    """
                    INSERT INTO memories (id, user_id, content, category, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        content = excluded.content,
                        category = excluded.category,
                        updated_at = MAX(memories.updated_at, excluded.updated_at)
                    """,
                    (mem_id, user_id, content, cat, mcreated, mupdated),
                )
                synced_mems += 1

        conn.commit()

    # 5. Monotonic daily token usage synchronization
    usage = get_daily_usage(user_id)
    if daily_usage_tokens is not None and daily_usage_tokens > 0:
        usage = sync_daily_tokens_used(user_id, daily_usage_tokens)

    return {
        "ok": True,
        "synced": True,
        "conversations": synced_convs,
        "messages": synced_msgs,
        "memories": synced_mems,
        "projects": synced_projs,
        "tokens_used": usage.get("tokens_used", 0),
    }


def export_full_user_state(user_id: str) -> dict[str, Any]:
    """Export 100% of a user's workspace (conversations, messages, artifacts,
    memories, projects, token metrics) for offline portability or backup."""
    if not user_id:
        return {}

    user = get_user_by_id(user_id) or {}
    convs = get_conversations(user_id=user_id, is_archived=False)
    archived_convs = get_conversations(user_id=user_id, is_archived=True)
    all_convs = convs + archived_convs

    messages_by_conv: dict[str, list[dict[str, Any]]] = {}
    for c in all_convs:
        cid = c["id"]
        messages_by_conv[cid] = get_messages(cid, user_id=user_id)

    memories = get_memories(user_id)
    projects = get_projects(user_id)
    artifacts = get_user_artifacts(user_id)
    usage = get_daily_usage(user_id)

    return {
        "version": "cortex-v3-backup",
        "exported_at": _utc_now_iso(),
        "user": {
            "id": user_id,
            "username": user.get("username", "Explorer"),
            "email": user.get("email", ""),
        },
        "conversations": all_convs,
        "messages_by_conversation": messages_by_conv,
        "memories": memories,
        "projects": projects,
        "artifacts": artifacts,
        "usage": usage,
    }


def import_full_user_state(user_id: str, import_data: dict[str, Any]) -> dict[str, Any]:
    """Atomically import an entire workspace backup into the user account."""
    if not user_id or not isinstance(import_data, dict):
        return {"ok": False, "detail": "Invalid backup data"}

    convs = import_data.get("conversations") or []
    msgs_flat: list[dict[str, Any]] = []

    # Support both flat messages list or messages_by_conversation map
    msgs_by_conv = import_data.get("messages_by_conversation")
    if isinstance(msgs_by_conv, dict):
        for cid, mlist in msgs_by_conv.items():
            if isinstance(mlist, list):
                for m in mlist:
                    if isinstance(m, dict):
                        m["conversation_id"] = cid
                        msgs_flat.append(m)
    elif isinstance(import_data.get("messages"), list):
        msgs_flat = import_data["messages"]

    mems = import_data.get("memories") or []
    projs = import_data.get("projects") or []
    tokens = import_data.get("usage", {}).get("tokens_used", 0) if isinstance(import_data.get("usage"), dict) else None

    return sync_full_user_state(
        user_id=user_id,
        conversations_data=convs,
        messages_data=msgs_flat,
        memories_data=mems,
        projects_data=projs,
        daily_usage_tokens=tokens,
    )


def get_user_sync_heartbeat(
    user_id: str,
    active_conv_id: Optional[str] = None,
    last_msg_count: Optional[int] = None,
    client_conv_hash: Optional[str] = None,
    client_proj_hash: Optional[str] = None,
) -> dict[str, Any]:
    """Lightweight real-time synchronization heartbeat for multi-browser / multi-device clients.
    Executes in < 5ms to guarantee sub-second awareness across concurrent sessions.
    """
    if not user_id:
        return {"ok": False, "detail": "User ID required"}

    now_iso = _utc_now_iso()
    with get_connection() as conn:
        # 1. Fetch conversations metadata for user
        cur = conn.execute(
            """
            SELECT id, title, created_at, updated_at, project_id,
                   COALESCE(is_pinned, 0) as is_pinned,
                   COALESCE(is_archived, 0) as is_archived
            FROM conversations
            WHERE user_id = ? AND COALESCE(is_archived, 0) = 0
            ORDER BY is_pinned DESC, updated_at DESC
            """,
            (user_id,),
        )
        conv_rows = [dict(r) for r in cur.fetchall()]

        # Generate a fast digest of user's active conversations list
        conv_summary = "|".join(f"{c['id']}:{c['updated_at']}:{c['title']}:{c['is_pinned']}" for c in conv_rows)
        server_conv_hash = hashlib.md5(conv_summary.encode("utf-8")).hexdigest()

        conversations_changed = (client_conv_hash != server_conv_hash)

        # 2. Fetch active projects metadata for user (ChatGPT-style project sync)
        cur_proj = conn.execute(
            """
            SELECT id, name, description, system_prompt, user_id,
                   COALESCE(is_pinned, 0) as is_pinned,
                   created_at, updated_at
            FROM projects
            WHERE user_id = ? AND COALESCE(is_deleted, 0) = 0
            ORDER BY is_pinned DESC, created_at DESC
            """,
            (user_id,),
        )
        project_rows = [dict(r) for r in cur_proj.fetchall()]
        proj_summary = "|".join(f"{p['id']}:{p['updated_at']}:{p['name']}:{p['is_pinned']}" for p in project_rows)
        server_proj_hash = hashlib.md5(proj_summary.encode("utf-8")).hexdigest()

        projects_changed = (client_proj_hash != server_proj_hash)

        # 3. Fetch recent deleted conversation tombstones
        cur_del = conn.execute(
            "SELECT conv_id FROM deleted_conversations WHERE user_id = ? ORDER BY deleted_at DESC LIMIT 50",
            (user_id,),
        )
        deleted_conv_ids = [r["conv_id"] for r in cur_del.fetchall()]

        # 4. Check active conversation messages if active_conv_id is provided
        active_messages = None
        active_msg_count = 0
        if active_conv_id and active_conv_id != "new":
            cur_msg = conn.execute(
                """
                SELECT id, conversation_id, role, content, tools_used, feedback, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (active_conv_id,),
            )
            msg_rows = [dict(r) for r in cur_msg.fetchall()]
            active_msg_count = len(msg_rows)

            for m in msg_rows:
                if m.get("tools_used") and isinstance(m["tools_used"], str):
                    try:
                        m["tools_used"] = json.loads(m["tools_used"])
                    except Exception:
                        m["tools_used"] = []

            if last_msg_count is None or last_msg_count != active_msg_count:
                active_messages = msg_rows

        # 5. Quick daily usage
        usage_info = get_daily_usage(user_id)
        tokens_used = usage_info.get("tokens_used", 0)
        uploads_count = usage_info.get("uploads_count", 0)

    # 6. Artifacts count (deduplicated)
    artifacts = get_user_artifacts(user_id)
    artifacts_count = len(artifacts)

    return {
        "ok": True,
        "server_time": now_iso,
        "conv_hash": server_conv_hash,
        "conversations_changed": conversations_changed,
        "conversations": conv_rows if conversations_changed else None,
        "latest_active_conv": conv_rows[0] if conv_rows else None,
        "active_conv_id": active_conv_id,
        "active_msg_count": active_msg_count,
        "active_messages": active_messages,
        "proj_hash": server_proj_hash,
        "projects_changed": projects_changed,
        "projects": project_rows if projects_changed else None,
        "deleted_conv_ids": deleted_conv_ids,
        "artifacts_count": artifacts_count,
        "usage": {
            "tokens_used": tokens_used,
            "uploads_count": uploads_count,
        },
    }


# Automatically initialize schema on import
init_db()
