import datetime
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_VERIFICATION_PURPOSE = "email_verification"
EMAIL_VERIFICATION_EXPIRE_HOURS = 24

ACCESS_TOKEN_PURPOSE = "access"
REFRESH_TOKEN_PURPOSE = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _create_token(user_id: uuid.UUID, purpose: str, expires_delta: datetime.timedelta) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "purpose": purpose,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str, purpose: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

    if payload.get("purpose") != purpose:
        return None

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None


def create_email_verification_token(user_id: uuid.UUID) -> str:
    return _create_token(
        user_id,
        EMAIL_VERIFICATION_PURPOSE,
        datetime.timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS),
    )


def decode_email_verification_token(token: str) -> uuid.UUID | None:
    return _decode_token(token, EMAIL_VERIFICATION_PURPOSE)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(
        user_id,
        ACCESS_TOKEN_PURPOSE,
        datetime.timedelta(minutes=settings.access_token_expire_minutes),
    )


def decode_access_token(token: str) -> uuid.UUID | None:
    return _decode_token(token, ACCESS_TOKEN_PURPOSE)


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(
        user_id,
        REFRESH_TOKEN_PURPOSE,
        datetime.timedelta(days=settings.refresh_token_expire_days),
    )


def decode_refresh_token(token: str) -> uuid.UUID | None:
    return _decode_token(token, REFRESH_TOKEN_PURPOSE)
