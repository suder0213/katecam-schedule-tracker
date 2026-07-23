import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_permission
from app.models.team import Team, TeamMember
from app.models.user import User, UserPermission
from app.schemas.auth import SignupResponse
from app.schemas.team import TeamCreate, TeamMemberCreate, TeamMemberResponse, TeamResponse

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> Team:
    team = Team(name=payload.name)
    db.add(team)
    db.commit()
    db.refresh(team)

    return team


@router.get("", response_model=list[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Team]:
    return db.query(Team).all()


@router.get("/mine", response_model=list[TeamResponse])
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Team]:
    return (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.team_id)
        .filter(TeamMember.user_id == current_user.user_id)
        .all()
    )


@router.get("/{team_id}/members", response_model=list[SignupResponse])
def list_team_members(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[User]:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")

    return (
        db.query(User)
        .join(TeamMember, TeamMember.user_id == User.user_id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )


@router.post(
    "/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED
)
def add_team_member(
    team_id: uuid.UUID,
    payload: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMember:
    if (
        current_user.permission == UserPermission.STUDENT
        and payload.user_id != current_user.user_id
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Students may only add themselves")

    if db.get(Team, team_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Team not found")

    if db.get(User, payload.user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    membership = TeamMember(team_id=team_id, user_id=payload.user_id)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "User is already a member of this team"
        ) from None

    db.refresh(membership)
    return membership


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.permission == UserPermission.STUDENT and user_id != current_user.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Students may only remove themselves")

    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membership not found")

    db.delete(membership)
    db.commit()
