import logging

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.crawl_texts import router as crawl_texts_router
from app.api.routes.schedule_proposals import router as schedule_proposals_router
from app.api.routes.schedules import router as schedules_router
from app.api.routes.teams import router as teams_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Katecam Todo Tracker")
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(teams_router)
app.include_router(schedules_router)
app.include_router(crawl_texts_router)
app.include_router(schedule_proposals_router)


@app.get("/health")
def health():
    return {"status": "ok"}
