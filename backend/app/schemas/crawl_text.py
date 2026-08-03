import datetime
import uuid

from pydantic import BaseModel, model_validator

from app.models.crawl_text import CrawlSource
from app.schemas.user import UserBriefResponse


class CrawlTextCreate(BaseModel):
    source: CrawlSource
    channel: str | None = None
    raw_text: str

    @model_validator(mode="after")
    def _channel_matches_source(self) -> "CrawlTextCreate":
        if self.source == CrawlSource.DISCORD and not self.channel:
            raise ValueError("channel is required when source is discord")
        if self.source == CrawlSource.NOTION and self.channel is not None:
            raise ValueError("channel must be omitted when source is notion")
        return self


class CrawlTextResponse(BaseModel):
    raw_text_id: uuid.UUID
    source: CrawlSource
    channel: str | None
    raw_text: str
    created_at: datetime.datetime
    created_by: UserBriefResponse | None

    model_config = {"from_attributes": True}
