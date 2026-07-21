import datetime
import uuid

from pydantic import BaseModel, Field

from app.models.schedule import ScheduleKind


class ScheduleCreate(BaseModel):
    kind: ScheduleKind
    title: str = Field(min_length=1)
    contents: str
    deadline: datetime.datetime


class ScheduleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    contents: str | None = None
    deadline: datetime.datetime | None = None


class ScheduleResponse(BaseModel):
    schedule_id: uuid.UUID
    kind: ScheduleKind
    title: str
    contents: str
    deadline: datetime.datetime
    owner_id: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class CalendarScheduleResponse(ScheduleResponse):
    done: bool


class ScheduleCompletionUpdate(BaseModel):
    done: bool


class ScheduleCompletionResponse(BaseModel):
    schedule_id: uuid.UUID
    owner_id: uuid.UUID
    done: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
