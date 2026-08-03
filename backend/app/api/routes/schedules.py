import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.schedule import Schedule, ScheduleCompletion, ScheduleKind
from app.models.user import User, UserPermission
from app.schemas.schedule import (
    CalendarScheduleResponse,
    ScheduleCompletionResponse,
    ScheduleCompletionUpdate,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _check_write_permission(current_user: User, schedule: Schedule) -> None:
    if schedule.kind == ScheduleKind.SHARED:
        if current_user.permission not in (UserPermission.MANAGER, UserPermission.DEV):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")
    else:
        if schedule.owner_id != current_user.user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")


def _visible_to(target_id: uuid.UUID):
    return or_(Schedule.kind == ScheduleKind.SHARED, Schedule.owner_id == target_id)


@router.get("", response_model=list[CalendarScheduleResponse])
def list_schedules(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    student_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if student_id is None:
        target_id = current_user.user_id
    else:
        if db.get(User, student_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        target_id = student_id

    # Anyone can look up anyone else's shared-schedule completion status, but a
    # person's personal schedules are visible only on their own calendar.
    is_own_calendar = target_id == current_user.user_id
    visibility = _visible_to(target_id) if is_own_calendar else Schedule.kind == ScheduleKind.SHARED

    month_start = datetime.datetime(year, month, 1, tzinfo=datetime.timezone.utc)
    if month == 12:
        month_end = datetime.datetime(year + 1, 1, 1, tzinfo=datetime.timezone.utc)
    else:
        month_end = datetime.datetime(year, month + 1, 1, tzinfo=datetime.timezone.utc)

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.deadline >= month_start,
            Schedule.deadline < month_end,
            visibility,
        )
        .order_by(Schedule.deadline)
        .all()
    )

    done_by_schedule_id = {
        completion.schedule_id: completion.done
        for completion in db.query(ScheduleCompletion).filter(
            ScheduleCompletion.owner_id == target_id,
            ScheduleCompletion.schedule_id.in_([s.schedule_id for s in schedules]),
        )
    }

    return [
        {
            "schedule_id": s.schedule_id,
            "kind": s.kind,
            "title": s.title,
            "contents": s.contents,
            "deadline": s.deadline,
            "owner_id": s.owner_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "done": done_by_schedule_id.get(s.schedule_id, False),
        }
        for s in schedules
    ]


@router.get("/todo", response_model=list[CalendarScheduleResponse])
def list_todo_schedules(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """사이드바 TODO 탭 — 본인 기준 미완료 일정을 마감일 임박순으로 반환(월 무관)."""
    target_id = current_user.user_id

    schedules = (
        db.query(Schedule)
        .outerjoin(
            ScheduleCompletion,
            (ScheduleCompletion.schedule_id == Schedule.schedule_id)
            & (ScheduleCompletion.owner_id == target_id),
        )
        .filter(
            _visible_to(target_id),
            or_(ScheduleCompletion.done.is_(None), ScheduleCompletion.done.is_(False)),
        )
        .order_by(Schedule.deadline)
        .limit(limit)
        .all()
    )

    return [
        {
            "schedule_id": s.schedule_id,
            "kind": s.kind,
            "title": s.title,
            "contents": s.contents,
            "deadline": s.deadline,
            "owner_id": s.owner_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "done": False,
        }
        for s in schedules
    ]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Schedule:
    if payload.kind == ScheduleKind.SHARED:
        if current_user.permission not in (UserPermission.MANAGER, UserPermission.DEV):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")
        owner_id = None
    else:
        owner_id = current_user.user_id

    schedule = Schedule(
        kind=payload.kind,
        title=payload.title,
        contents=payload.contents,
        deadline=payload.deadline,
        owner_id=owner_id,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: uuid.UUID,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Schedule:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule not found")

    _check_write_permission(current_user, schedule)

    if payload.title is not None:
        schedule.title = payload.title
    if payload.contents is not None:
        schedule.contents = payload.contents
    if payload.deadline is not None:
        schedule.deadline = payload.deadline

    db.commit()
    db.refresh(schedule)

    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule not found")

    _check_write_permission(current_user, schedule)

    db.delete(schedule)
    db.commit()


@router.put("/{schedule_id}/completion", response_model=ScheduleCompletionResponse)
def update_schedule_completion(
    schedule_id: uuid.UUID,
    payload: ScheduleCompletionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScheduleCompletion:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule not found")

    if schedule.kind == ScheduleKind.PERSONAL and schedule.owner_id != current_user.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permission")

    completion = (
        db.query(ScheduleCompletion)
        .filter(
            ScheduleCompletion.schedule_id == schedule_id,
            ScheduleCompletion.owner_id == current_user.user_id,
        )
        .first()
    )
    if completion is None:
        completion = ScheduleCompletion(
            schedule_id=schedule_id, owner_id=current_user.user_id, done=payload.done
        )
        db.add(completion)
    else:
        completion.done = payload.done

    db.commit()
    db.refresh(completion)

    return completion
