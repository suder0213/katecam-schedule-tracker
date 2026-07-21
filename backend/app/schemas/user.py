from pydantic import BaseModel

from app.models.user import UserPermission


class UpdatePermissionRequest(BaseModel):
    permission: UserPermission
