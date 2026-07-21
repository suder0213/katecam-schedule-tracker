import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

REQUEST_LIMIT = 10
WINDOW_SECONDS = 1
BLOCK_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, tuple[float, int]] = {}
        self._blocked_until: dict[str, float] = {}

    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()

        blocked_until = self._blocked_until.get(key)
        if blocked_until is not None and now < blocked_until:
            return JSONResponse({"detail": "Too many requests. Try again later."}, status_code=429)

        window_start, count = self._windows.get(key, (now, 0))
        if now - window_start >= WINDOW_SECONDS:
            window_start, count = now, 1
        else:
            count += 1
            if count > REQUEST_LIMIT:
                self._blocked_until[key] = now + BLOCK_SECONDS
                return JSONResponse(
                    {"detail": "Too many requests. Try again later."}, status_code=429
                )

        self._windows[key] = (window_start, count)
        return await call_next(request)
