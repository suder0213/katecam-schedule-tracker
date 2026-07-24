import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.schedule import Schedule, ScheduleKind
from app.models.schedule_proposal import ProposalStatus, ScheduleProposal
from app.models.user import UserPermission
from app.schemas.schedule_proposal import ScheduleProposalResponse, ScheduleProposalUpdate

router = APIRouter(prefix="/schedule-proposals", tags=["schedule-proposals"])


@router.get("", response_model=list[ScheduleProposalResponse])
def list_schedule_proposals(
    raw_text_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> list[ScheduleProposal]:
    query = db.query(ScheduleProposal)
    if raw_text_id is not None:
        query = query.filter(ScheduleProposal.raw_text_id == raw_text_id)

    return query.order_by(ScheduleProposal.created_at).all()


@router.patch("/{proposal_id}", response_model=ScheduleProposalResponse)
def update_schedule_proposal(
    proposal_id: uuid.UUID,
    payload: ScheduleProposalUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> ScheduleProposal:
    proposal = db.get(ScheduleProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposal not found")

    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only pending proposals can be edited")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(proposal, field, value)

    db.commit()
    db.refresh(proposal)

    return proposal


@router.post("/{proposal_id}/approve", response_model=ScheduleProposalResponse)
def approve_schedule_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> ScheduleProposal:
    proposal = db.get(ScheduleProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposal not found")

    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposal already processed")

    schedule = Schedule(
        kind=ScheduleKind.SHARED,
        title=proposal.title,
        contents=proposal.contents,
        deadline=proposal.deadline,
        owner_id=None,
    )
    db.add(schedule)
    proposal.status = ProposalStatus.APPROVED

    try:
        db.commit()
    except Exception:
        db.rollback()
        proposal.status = ProposalStatus.PENDING
        db.commit()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to apply proposal")

    db.refresh(proposal)
    return proposal


@router.post("/{proposal_id}/reject", response_model=ScheduleProposalResponse)
def reject_schedule_proposal(
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> ScheduleProposal:
    proposal = db.get(ScheduleProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposal not found")

    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposal already processed")

    proposal.status = ProposalStatus.REJECTED
    db.commit()
    db.refresh(proposal)

    return proposal
