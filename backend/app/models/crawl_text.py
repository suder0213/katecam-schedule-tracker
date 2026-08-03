import enum
import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class CrawlSource(str, enum.Enum):
    NOTION = "notion"
    DISCORD = "discord"


class CrawlText(CreatedAtMixin, Base):
    __tablename__ = "crawl_texts"
    __table_args__ = (
        CheckConstraint(
            "(source = 'DISCORD' AND channel IS NOT NULL) "
            "OR (source = 'NOTION' AND channel IS NULL)",
            name="ck_crawl_text_channel_matches_source",
        ),
    )

    raw_text_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[CrawlSource] = mapped_column(
        Enum(CrawlSource, name="crawl_source"), nullable=False
    )
    channel: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_text: Mapped[str] = mapped_column(String, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    created_by = relationship("User", foreign_keys=[created_by_id])
