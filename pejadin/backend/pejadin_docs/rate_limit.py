import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_clients=10000, clock=time.monotonic):
        self._events = defaultdict(deque)
        self._max_clients = max_clients
        self._clock = clock
        self._lock = threading.Lock()
        self._next_cleanup = 0

    def allow(self, key, limit, window_seconds):
        now = self._clock()
        cutoff = now - window_seconds
        with self._lock:
            if now >= self._next_cleanup:
                for client_key in list(self._events):
                    events = self._events[client_key]
                    while events and events[0] <= cutoff:
                        events.popleft()
                    if not events:
                        del self._events[client_key]
                self._next_cleanup = now + 60
            else:
                events = self._events.get(key)
                if events is not None:
                    while events and events[0] <= cutoff:
                        events.popleft()
                    if not events:
                        del self._events[key]
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self._max_clients:
                    return False
                events = self._events[key]
            if len(events) >= limit:
                return False
            events.append(now)
            return True


def request_rate_limit(method, path):
    if method == "POST" and path in ("/api/login", "/api/v1/auth/login"):
        return "login", 5
    if method == "GET" and path.endswith("/pdf/lengkap"):
        return "full-pdf", 3
    return None
