import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User, UserPermission
from app.schemas.auth import SignupResponse
from app.schemas.user import UpdatePermissionRequest

router = APIRouter(prefix="/users", tags=["users"])

CHANGEABLE_PERMISSIONS = {UserPermission.STUDENT, UserPermission.MANAGER}


@router.get("/me", response_model=SignupResponse)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("", response_model=list[SignupResponse])
def list_students(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    return (
        db.query(User)
        .filter(User.permission == UserPermission.STUDENT)
        .order_by(User.nick_name)
        .all()
    )


@router.get("/all", response_model=list[SignupResponse])
def list_all_users(
    _current_user: User = Depends(require_permission(UserPermission.DEV)),
    db: Session = Depends(get_db),
) -> list[User]:
    return db.query(User).order_by(User.nick_name).all()


@router.get("/{user_id}", response_model=SignupResponse)
def read_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return target


@router.patch("/{user_id}/permission", response_model=SignupResponse)
def update_user_permission(
    user_id: uuid.UUID,
    payload: UpdatePermissionRequest,
    current_user: User = Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
    db: Session = Depends(get_db),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if (
        payload.permission not in CHANGEABLE_PERMISSIONS
        or target.permission not in CHANGEABLE_PERMISSIONS
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "dev permission cannot be changed via this endpoint"
        )

    target.permission = payload.permission
    db.commit()
    db.refresh(target)

    return target
