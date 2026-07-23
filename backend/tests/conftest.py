import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.core.config import settings
from app.core.rate_limit import reset_rate_limit_state
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.user import User, UserPermission

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/katecam_test"

TABLES_IN_FK_ORDER = (
    "schedule_proposals",
    "crawl_texts",
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

# drop_all + create_all (not just create_all) so a stale test DB from a prior
# model change always gets rebuilt to match the current models exactly.
Base.metadata.drop_all(bind=engine)
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


@pytest.fixture()
def make_user():
    """Creates an already-verified user directly in the DB, bypassing signup/verify."""

    def _make(
        email: str,
        permission: UserPermission = UserPermission.STUDENT,
        nick_name: str | None = None,
    ) -> User:
        db = TestingSessionLocal()
        try:
            user = User(
                email=email,
                password=hash_password("password123"),
                nick_name=nick_name or email.split("@")[0],
                permission=permission,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    return _make


@pytest.fixture()
def auth_header():
    def _header(user: User) -> dict:
        return {"Authorization": f"Bearer {create_access_token(user.user_id)}"}

    return _header


@pytest.fixture()
def db_session():
    """Direct DB access for test setup that has no API endpoint yet (e.g. team assignment)."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
