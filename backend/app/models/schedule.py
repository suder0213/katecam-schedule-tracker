import datetime
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ScheduleKind(str, enum.Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class Schedule(TimestampMixin, Base):
    __tablename__ = "schedules"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[ScheduleKind] = mapped_column(
        Enum(ScheduleKind, name="schedule_kind"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    contents: Mapped[str] = mapped_column(String, nullable=False)
    deadline: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )


class ScheduleCompletion(TimestampMixin, Base):
    __tablename__ = "schedule_completions"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.schedule_id"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
