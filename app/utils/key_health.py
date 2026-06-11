import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional

import app.config.settings as settings


@dataclass
class KeyHealth:
    key_prefix: str
    status: str = "healthy"
    success_count: int = 0
    failure_count: int = 0
    last_success_at: Optional[float] = None
    last_failure_at: Optional[float] = None
    cooldown_until: Optional[float] = None
    last_error: str = ""
    status_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class KeyHealthManager:
    def __init__(self):
        self._items: Dict[str, KeyHealth] = {}
        self._lock = Lock()

    def ensure(self, api_key: str) -> KeyHealth:
        with self._lock:
            if api_key not in self._items:
                self._items[api_key] = KeyHealth(key_prefix=self._mask(api_key))
            return self._items[api_key]

    def is_available(self, api_key: str) -> bool:
        item = self.ensure(api_key)
        if item.cooldown_until and item.cooldown_until > time.time():
            return False
        return item.status not in {"invalid", "region_blocked"}

    def record_success(self, api_key: str) -> None:
        with self._lock:
            item = self._items.setdefault(api_key, KeyHealth(key_prefix=self._mask(api_key)))
            item.status = "healthy"
            item.success_count += 1
            item.last_success_at = time.time()
            item.cooldown_until = None
            item.last_error = ""

    def record_failure(self, api_key: str, error: str = "", status_code: Optional[int] = None) -> None:
        now = time.time()
        status = self._classify(error, status_code)
        cooldown = self._cooldown_seconds(status)
        with self._lock:
            item = self._items.setdefault(api_key, KeyHealth(key_prefix=self._mask(api_key)))
            item.status = status
            item.failure_count += 1
            item.last_failure_at = now
            item.last_error = str(error)[:500]
            item.status_counts[status] += 1
            item.cooldown_until = now + cooldown if cooldown > 0 else None

    def get_stats(self, api_keys=None):
        now = time.time()
        with self._lock:
            keys = api_keys if api_keys is not None else list(self._items.keys())
            rows = []
            for api_key in keys:
                item = self._items.get(api_key)
                if item is None:
                    item = KeyHealth(key_prefix=self._mask(api_key))
                cooldown_remaining = max(0, int((item.cooldown_until or 0) - now))
                display_status = item.status
                if display_status == "cooling" and cooldown_remaining == 0:
                    display_status = "healthy"
                rows.append(
                    {
                        "api_key": item.key_prefix,
                        "status": display_status,
                        "success_count": item.success_count,
                        "failure_count": item.failure_count,
                        "last_success_at": item.last_success_at,
                        "last_failure_at": item.last_failure_at,
                        "cooldown_remaining": cooldown_remaining,
                        "last_error": item.last_error,
                        "status_counts": dict(item.status_counts),
                    }
                )
            return rows

    def _classify(self, error: str, status_code: Optional[int]) -> str:
        text = str(error).lower()
        if status_code == 401 or "api key not valid" in text or "invalid api key" in text:
            return "invalid"
        if status_code == 400 and "user location is not supported" in text:
            return "cooling"
        if status_code == 429 or "quota" in text or "配额" in text:
            return "quota_exceeded"
        if status_code in {500, 502, 503, 504} or "timeout" in text or "超时" in text:
            return "cooling"
        return "cooling"

    def _cooldown_seconds(self, status: str) -> int:
        if status in {"invalid", "region_blocked"}:
            return 0
        if status == "quota_exceeded":
            return int(getattr(settings, "KEY_QUOTA_COOLDOWN_SECONDS", 3600))
        return int(getattr(settings, "KEY_FAILURE_COOLDOWN_SECONDS", 60))

    def _mask(self, api_key: str) -> str:
        if not api_key:
            return ""
        return f"{api_key[:8]}...{api_key[-3:]}"


key_health_manager = KeyHealthManager()
