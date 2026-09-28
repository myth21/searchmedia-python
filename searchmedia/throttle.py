"""One request per time window per client IP, tracked in an in-memory dict under a lock.
A dict is enough: the process lives long, and losing the limits on restart is fine."""

import random
import threading
import time

ONE_REQUEST_IN_SECONDS = 5.0
ENTRY_TTL_SECONDS = 3600.0
GARBAGE_COLLECTION_CHANCE = 1 / 100


class RequestTooSoon(Exception):
    pass


class RequestThrottle:
    def __init__(self, seconds: float = ONE_REQUEST_IN_SECONDS) -> None:
        self._seconds = seconds
        self._lock = threading.Lock()
        self._last_request_at: dict[str, float] = {}

    def throttle_by_ip(self, ip: str) -> None:
        now = time.monotonic()

        with self._lock:
            last = self._last_request_at.get(ip)

            if last is not None and now - last < self._seconds:
                raise RequestTooSoon(
                    f"More than one request in {self._seconds:.0f} seconds by ip."
                )

            self._last_request_at[ip] = now

            if random.random() < GARBAGE_COLLECTION_CHANCE:
                self._evict_expired(now)

    def _evict_expired(self, now: float) -> None:
        expired = [
            ip for ip, at in self._last_request_at.items() if now - at > ENTRY_TTL_SECONDS
        ]

        for ip in expired:
            del self._last_request_at[ip]
