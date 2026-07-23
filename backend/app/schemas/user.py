from pydantic import BaseModel, Field

from app.models.user import UserPermission


class UpdatePermissionRequest(BaseModel):
    permission: UserPermission


class UpdateNicknameRequest(BaseModel):
    nick_name: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
