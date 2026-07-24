import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.agent import AgentParseError, analyze_crawl_text
from app.models.crawl_text import CrawlText
from app.models.schedule_proposal import ScheduleProposal
from app.models.user import UserPermission
from app.schemas.crawl_text import CrawlTextCreate, CrawlTextResponse
from app.schemas.schedule_proposal import ScheduleProposalResponse

router = APIRouter(prefix="/crawl-texts", tags=["crawl-texts"])


@router.post("", response_model=CrawlTextResponse, status_code=status.HTTP_201_CREATED)
def create_crawl_text(
    payload: CrawlTextCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> CrawlText:
    crawl_text = CrawlText(
        source=payload.source,
        channel=payload.channel,
        raw_text=payload.raw_text,
    )
    db.add(crawl_text)
    db.commit()
    db.refresh(crawl_text)

    return crawl_text


@router.get("/{raw_text_id}", response_model=CrawlTextResponse)
def read_crawl_text(
    raw_text_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> CrawlText:
    crawl_text = db.get(CrawlText, raw_text_id)
    if crawl_text is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crawl text not found")

    return crawl_text


@router.post(
    "/{raw_text_id}/analyze",
    response_model=list[ScheduleProposalResponse],
    status_code=status.HTTP_201_CREATED,
)
def analyze_text(
    raw_text_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.MANAGER, UserPermission.DEV)),
) -> list[ScheduleProposal]:
    crawl_text = db.get(CrawlText, raw_text_id)
    if crawl_text is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crawl text not found")

    try:
        items = analyze_crawl_text(crawl_text)
    except AgentParseError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "파싱 실패") from e

    proposals = [
        ScheduleProposal(
            raw_text_id=crawl_text.raw_text_id,
            title=item.title,
            contents=item.contents,
            deadline=item.deadline,
        )
        for item in items
    ]
    db.add_all(proposals)
    db.commit()
    for proposal in proposals:
        db.refresh(proposal)

    return proposals
