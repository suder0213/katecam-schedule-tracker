import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.core.rate_limit import reset_rate_limit_state
from app.db.base import Base
from app.main import app

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/katecam_test"

TABLES_IN_FK_ORDER = (
    "schedule_completions",
    "schedules",
    "team_members",
    "teams",
    "users",
)


def _ensure_test_database() -> None:
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'katecam_test'")
        ).first()
        if exists is None:
            conn.execute(text("CREATE DATABASE katecam_test"))
    admin_engine.dispose()


_ensure_test_database()

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _clean_state():
    reset_rate_limit_state()
    yield
    with engine.begin() as conn:
        for table in TABLES_IN_FK_ORDER:
            conn.execute(text(f"DELETE FROM {table}"))


@pytest.fixture()
def client():
    # https base_url so httpx's cookie jar will resend our Secure refresh cookie
    # on subsequent requests within the same test (real login/refresh flow relies on this).
    return TestClient(app, base_url="https://testserver")
