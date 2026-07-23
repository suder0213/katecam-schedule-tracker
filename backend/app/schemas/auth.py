import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserPermission


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nick_name: str | None = None


class SignupResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    nick_name: str | None
    permission: UserPermission
    is_verified: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
