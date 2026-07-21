import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class UserPermission(str, enum.Enum):
    DEV = "dev"
    MANAGER = "manager"
    STUDENT = "student"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    nick_name: Mapped[str | None] = mapped_column(String, nullable=True)
    permission: Mapped[UserPermission] = mapped_column(
        Enum(UserPermission, name="user_permission"),
        nullable=False,
        default=UserPermission.STUDENT,
    )
