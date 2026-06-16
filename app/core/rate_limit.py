import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone

RATE_LIMIT_WINDOW = timedelta(minutes=15)
RATE_LIMIT_MAX = 5

_failed_attempts: dict[str, list[datetime]] = defaultdict(list)
_lock = threading.Lock()


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """Returns (is_limited, retry_after_seconds). Prunes stale entries first."""
    now = datetime.now(timezone.utc)
    cutoff = now - RATE_LIMIT_WINDOW
    with _lock:
        _failed_attempts[ip] = [t for t in _failed_attempts[ip] if t > cutoff]
        count = len(_failed_attempts[ip])
        if count >= RATE_LIMIT_MAX:
            oldest = _failed_attempts[ip][0]
            retry_after = int((oldest + RATE_LIMIT_WINDOW - now).total_seconds()) + 1
            return True, max(retry_after, 1)
        return False, 0


def record_failed_attempt(ip: str) -> None:
    with _lock:
        _failed_attempts[ip].append(datetime.now(timezone.utc))


def reset_for_ip(ip: str) -> None:
    with _lock:
        _failed_attempts.pop(ip, None)
