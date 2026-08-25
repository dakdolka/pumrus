from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Small single-instance guard for sensitive and high-write endpoints."""

    def __init__(self, app):
        super().__init__(app)
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()

    @staticmethod
    def _bucket(path: str) -> tuple[str, int, int] | None:
        if "/v2/admin" in path:
            return "admin", 300, 300
        if path.endswith("/v2/auth/telegram"):
            return "auth", 30, 60
        if "/v2/payments/checkout" in path:
            return "checkout", 20, 60
        if "/attempts" in path:
            return "attempt", 240, 60
        return None

    async def dispatch(self, request, call_next):
        policy = self._bucket(request.url.path)
        if policy is None:
            return await call_next(request)
        bucket, maximum, window = policy
        # Uvicorn resolves trusted proxy headers before the request reaches the
        # application. Reading X-Forwarded-For here would let a direct client
        # spoof a new address for every request and bypass the limiter.
        address = request.client.host if request.client else "unknown"
        key = (bucket, address)
        now = time.monotonic()
        async with self._lock:
            if now - self._last_cleanup >= 300:
                stale = [
                    stale_key
                    for stale_key, stale_events in self._events.items()
                    if not stale_events or stale_events[-1] <= now - 300
                ]
                for stale_key in stale:
                    self._events.pop(stale_key, None)
                self._last_cleanup = now
            events = self._events[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= maximum:
                return JSONResponse(
                    {"detail": "Слишком много запросов. Попробуйте чуть позже."},
                    status_code=429,
                    headers={"Retry-After": str(window)},
                )
            events.append(now)
        return await call_next(request)
