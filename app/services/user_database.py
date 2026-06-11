import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import app.config.settings as settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.USER_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );

                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    key_prefix TEXT NOT NULL,
                    quota_daily INTEGER NOT NULL DEFAULT 1000,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    total_requests INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS api_key_daily_usage (
                    key_id INTEGER NOT NULL,
                    usage_date TEXT NOT NULL,
                    requests INTEGER NOT NULL DEFAULT 0,
                    tokens INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (key_id, usage_date),
                    FOREIGN KEY(key_id) REFERENCES user_api_keys(id) ON DELETE CASCADE
                );
                """
            )

    def create_user(self, username: str, password: str, is_admin: bool = False):
        username = self._normalize_username(username)
        self._validate_password(password)
        password_hash = self._hash_password(password)
        with self.connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, is_admin, is_active, created_at)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (username, password_hash, int(is_admin), _now()),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("username already exists") from exc
            user_id = int(cursor.lastrowid)
        self.add_audit_log(user_id, "user.register", {"username": username})
        return self.get_user(user_id)

    def ensure_admin_user(self, username: str, password: str):
        username = self._normalize_username(username)
        self._validate_password(password)
        password_hash = self._hash_password(password)
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE users
                    SET password_hash = ?, is_admin = 1, is_active = 1
                    WHERE id = ?
                    """,
                    (password_hash, row["id"]),
                )
                user_id = int(row["id"])
                action = "admin.ensure.update"
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, password_hash, is_admin, is_active, created_at)
                    VALUES (?, ?, 1, 1, ?)
                    """,
                    (username, password_hash, _now()),
                )
                user_id = int(cursor.lastrowid)
                action = "admin.ensure.create"
        self.add_audit_log(user_id, action, {"username": username})
        return self.get_user(user_id)

    def authenticate_user(self, username: str, password: str):
        username = self._normalize_username(username)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,),
            ).fetchone()
            if not row or not self._verify_password(password, row["password_hash"]):
                return None
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_now(), row["id"]))
            user_id = int(row["id"])
        self.add_audit_log(user_id, "user.login", {"username": username})
        return self.get_user(user_id)

    def get_user(self, user_id: int):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, username, is_admin, is_active, created_at, last_login_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    def create_api_key(self, user_id: int, name: str, quota_daily: Optional[int] = None):
        name = (name or "default").strip()[:80] or "default"
        quota = int(quota_daily or settings.USER_API_KEY_DEFAULT_DAILY_QUOTA)
        raw_key = "sk-user-" + secrets.token_urlsafe(32)
        key_hash = self._hash_api_key(raw_key)
        key_prefix = raw_key[:16]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO user_api_keys
                    (user_id, name, key_hash, key_prefix, quota_daily, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (user_id, name, key_hash, key_prefix, quota, _now()),
            )
        self.add_audit_log(user_id, "api_key.create", {"name": name, "key_prefix": key_prefix})
        return {"api_key": raw_key, "key_prefix": key_prefix, "name": name, "quota_daily": quota}

    def list_api_keys(self, user_id: int):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, key_prefix, quota_daily, is_active, created_at, last_used_at,
                       total_requests, total_tokens
                FROM user_api_keys
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_users(self, limit: int = 100, offset: int = 0):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.is_admin, u.is_active, u.created_at, u.last_login_at,
                       COUNT(k.id) AS api_key_count,
                       COALESCE(SUM(k.total_requests), 0) AS total_requests,
                       COALESCE(SUM(k.total_tokens), 0) AS total_tokens
                FROM users u
                LEFT JOIN user_api_keys k ON k.user_id = u.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (min(max(int(limit), 1), 500), max(int(offset), 0)),
            ).fetchall()
            return [dict(row) for row in rows]

    def update_user(self, user_id: int, is_active: Optional[bool] = None, is_admin: Optional[bool] = None):
        fields = []
        values = []
        if is_active is not None:
            fields.append("is_active = ?")
            values.append(int(is_active))
        if is_admin is not None:
            fields.append("is_admin = ?")
            values.append(int(is_admin))
        if not fields:
            return self.get_user(user_id)
        values.append(user_id)
        with self.connect() as conn:
            cursor = conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
            if cursor.rowcount == 0:
                return None
        self.add_audit_log(user_id, "admin.user.update", {"is_active": is_active, "is_admin": is_admin})
        return self.get_user(user_id)

    def list_all_api_keys(self, limit: int = 100, offset: int = 0):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT k.id, k.user_id, u.username, k.name, k.key_prefix, k.quota_daily,
                       k.is_active, k.created_at, k.last_used_at, k.total_requests, k.total_tokens
                FROM user_api_keys k
                JOIN users u ON u.id = k.user_id
                ORDER BY k.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (min(max(int(limit), 1), 500), max(int(offset), 0)),
            ).fetchall()
            return [dict(row) for row in rows]

    def update_api_key(self, key_id: int, is_active: Optional[bool] = None, quota_daily: Optional[int] = None):
        fields = []
        values = []
        if is_active is not None:
            fields.append("is_active = ?")
            values.append(int(is_active))
        if quota_daily is not None:
            fields.append("quota_daily = ?")
            values.append(max(int(quota_daily), 0))
        if not fields:
            return self.get_api_key(key_id)
        values.append(key_id)
        with self.connect() as conn:
            cursor = conn.execute(f"UPDATE user_api_keys SET {', '.join(fields)} WHERE id = ?", values)
            if cursor.rowcount == 0:
                return None
            row = conn.execute(
                """
                SELECT k.id, k.user_id, u.username, k.name, k.key_prefix, k.quota_daily,
                       k.is_active, k.created_at, k.last_used_at, k.total_requests, k.total_tokens
                FROM user_api_keys k
                JOIN users u ON u.id = k.user_id
                WHERE k.id = ?
                """,
                (key_id,),
            ).fetchone()
            result = dict(row) if row else None
        if result:
            self.add_audit_log(result["user_id"], "admin.api_key.update", {"key_id": key_id, "is_active": is_active, "quota_daily": quota_daily})
        return result

    def get_api_key(self, key_id: int):
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT k.id, k.user_id, u.username, k.name, k.key_prefix, k.quota_daily,
                       k.is_active, k.created_at, k.last_used_at, k.total_requests, k.total_tokens
                FROM user_api_keys k
                JOIN users u ON u.id = k.user_id
                WHERE k.id = ?
                """,
                (key_id,),
            ).fetchone()
            return dict(row) if row else None

    def revoke_api_key(self, user_id: int, key_id: int):
        with self.connect() as conn:
            cursor = conn.execute(
                "UPDATE user_api_keys SET is_active = 0 WHERE id = ? AND user_id = ?",
                (key_id, user_id),
            )
            revoked = cursor.rowcount > 0
        if revoked:
            self.add_audit_log(user_id, "api_key.revoke", {"key_id": key_id})
        return revoked

    def validate_api_key(self, raw_key: str):
        key_hash = self._hash_api_key(raw_key)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT k.*, u.username, u.is_active AS user_active
                FROM user_api_keys k
                JOIN users u ON u.id = k.user_id
                WHERE k.key_hash = ? AND k.is_active = 1 AND u.is_active = 1
                """,
                (key_hash,),
            ).fetchone()
            if not row:
                return None
            record = dict(row)
            if record["quota_daily"] > 0 and self.get_api_key_usage_today(record["id"]) >= record["quota_daily"]:
                return None
            return record

    def record_api_key_usage(self, key_id: int, tokens: int = 0):
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE user_api_keys
                SET total_requests = total_requests + 1,
                    total_tokens = total_tokens + ?,
                    last_used_at = ?
                WHERE id = ?
                """,
                (int(tokens or 0), _now(), key_id),
            )
            conn.execute(
                "INSERT INTO audit_logs (user_id, action, detail, created_at) SELECT user_id, ?, ?, ? FROM user_api_keys WHERE id = ?",
                ("api_key.use", json.dumps({"key_id": key_id, "tokens": int(tokens or 0)}, ensure_ascii=False), _now(), key_id),
            )
            conn.execute(
                """
                INSERT INTO api_key_daily_usage (key_id, usage_date, requests, tokens)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(key_id, usage_date) DO UPDATE SET
                    requests = requests + 1,
                    tokens = tokens + excluded.tokens
                """,
                (key_id, datetime.now(timezone.utc).date().isoformat(), int(tokens or 0)),
            )

    def get_api_key_usage_today(self, key_id: int) -> int:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT requests
                FROM api_key_daily_usage
                WHERE key_id = ? AND usage_date = ?
                """,
                (key_id, datetime.now(timezone.utc).date().isoformat()),
            ).fetchone()
            return int(row["requests"] or 0) if row else 0

    def add_audit_log(self, user_id: Optional[int], action: str, detail=None):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (user_id, action, json.dumps(detail or {}, ensure_ascii=False), _now()),
            )

    def list_audit_logs(self, user_id: int, limit: int = 50):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, action, detail, created_at
                FROM audit_logs
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, min(max(int(limit), 1), 200)),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_all_audit_logs(self, limit: int = 100):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT l.id, l.user_id, u.username, l.action, l.detail, l.created_at
                FROM audit_logs l
                LEFT JOIN users u ON u.id = l.user_id
                ORDER BY l.id DESC
                LIMIT ?
                """,
                (min(max(int(limit), 1), 500),),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_summary(self):
        with self.connect() as conn:
            users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
            active_users = conn.execute("SELECT COUNT(*) AS count FROM users WHERE is_active = 1").fetchone()["count"]
            admins = conn.execute("SELECT COUNT(*) AS count FROM users WHERE is_admin = 1").fetchone()["count"]
            active_keys = conn.execute(
                "SELECT COUNT(*) AS count FROM user_api_keys WHERE is_active = 1"
            ).fetchone()["count"]
            total_keys = conn.execute("SELECT COUNT(*) AS count FROM user_api_keys").fetchone()["count"]
            total_requests = conn.execute(
                "SELECT COALESCE(SUM(total_requests), 0) AS count FROM user_api_keys"
            ).fetchone()["count"]
            total_tokens = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) AS count FROM user_api_keys"
            ).fetchone()["count"]
        return {
            "users": int(users or 0),
            "active_users": int(active_users or 0),
            "admins": int(admins or 0),
            "total_api_keys": int(total_keys or 0),
            "active_api_keys": int(active_keys or 0),
            "total_requests": int(total_requests or 0),
            "total_tokens": int(total_tokens or 0),
        }

    def create_session_token(self, user: dict) -> str:
        payload = json.dumps(
            {"user_id": user["id"], "username": user["username"], "is_admin": bool(user["is_admin"]), "iat": _now()},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        signature = hmac.new(self._session_secret(), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"

    def verify_session_token(self, token: str):
        if not token or "." not in token:
            return None
        payload_b64, signature = token.rsplit(".", 1)
        expected = hmac.new(self._session_secret(), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        try:
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        except Exception:
            return None
        if not self._session_is_fresh(payload.get("iat")):
            return None
        return self.get_user(int(payload.get("user_id") or 0))

    def _normalize_username(self, username: str) -> str:
        username = (username or "").strip().lower()
        if len(username) < 3 or len(username) > 40:
            raise ValueError("username must be 3-40 characters")
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-@.")
        if any(char not in allowed for char in username):
            raise ValueError("username contains invalid characters")
        return username

    def _validate_password(self, password: str):
        if not password or len(password) < 8:
            raise ValueError("password must be at least 8 characters")

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"

    def _verify_password(self, password: str, encoded: str) -> bool:
        try:
            algorithm, salt_b64, digest_b64 = encoded.split("$", 2)
            if algorithm != "pbkdf2_sha256":
                return False
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(digest_b64)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False

    def _hash_api_key(self, raw_key: str) -> str:
        return hmac.new(self._session_secret(), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()

    def _session_secret(self) -> bytes:
        return (settings.WEB_PASSWORD or settings.PASSWORD or "gemini-app").encode("utf-8")

    def _session_is_fresh(self, issued_at: str) -> bool:
        ttl = int(getattr(settings, "USER_SESSION_TTL_SECONDS", 7 * 24 * 3600))
        if ttl <= 0:
            return True
        try:
            issued_dt = datetime.fromisoformat(issued_at)
        except Exception:
            return False
        if issued_dt.tzinfo is None:
            issued_dt = issued_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - issued_dt <= timedelta(seconds=ttl)


user_db = UserDatabase()
