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
def list_users(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    # Sorted in Python, not SQL: the DB's en_US.utf8 collation doesn't order Hangul
    # the way a Korean dictionary does, but Python's codepoint order does, since the
    # Unicode Hangul Syllables block is laid out by (initial, medial, final).
    return sorted(db.query(User).all(), key=lambda u: u.nick_name or u.email)


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
