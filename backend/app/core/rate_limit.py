import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

REQUEST_LIMIT = 10
WINDOW_SECONDS = 1
BLOCK_SECONDS = 60

_windows: dict[str, tuple[float, int]] = {}
_blocked_until: dict[str, float] = {}


def reset_rate_limit_state() -> None:
    """Test-only hook: clears in-memory counters between test cases."""
    _windows.clear()
    _blocked_until.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()

        blocked_until = _blocked_until.get(key)
        if blocked_until is not None and now < blocked_until:
            return JSONResponse({"detail": "Too many requests. Try again later."}, status_code=429)

        window_start, count = _windows.get(key, (now, 0))
        if now - window_start >= WINDOW_SECONDS:
            window_start, count = now, 1
        else:
            count += 1
            if count > REQUEST_LIMIT:
                _blocked_until[key] = now + BLOCK_SECONDS
                return JSONResponse(
                    {"detail": "Too many requests. Try again later."}, status_code=429
                )

        _windows[key] = (window_start, count)
        return await call_next(request)
