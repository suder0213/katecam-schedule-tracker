import datetime
import uuid

from pydantic import BaseModel

from app.models.schedule_proposal import ProposalStatus


class ScheduleProposalUpdate(BaseModel):
    title: str | None = None
    contents: str | None = None
    deadline: datetime.datetime | None = None


class ScheduleProposalResponse(BaseModel):
    proposal_id: uuid.UUID
    raw_text_id: uuid.UUID
    title: str
    contents: str
    deadline: datetime.datetime
    status: ProposalStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
