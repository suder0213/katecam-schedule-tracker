import logging

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Katecam Todo Tracker")
app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "ok"}
