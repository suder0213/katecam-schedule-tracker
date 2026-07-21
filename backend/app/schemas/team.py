import datetime
import uuid

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=1)


class TeamResponse(BaseModel):
    team_id: uuid.UUID
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class TeamMemberCreate(BaseModel):
    user_id: uuid.UUID


class TeamMemberResponse(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
