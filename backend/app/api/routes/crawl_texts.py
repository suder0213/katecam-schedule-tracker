from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.models.crawl_text import CrawlText
from app.models.user import UserPermission
from app.schemas.crawl_text import CrawlTextCreate, CrawlTextResponse

router = APIRouter(prefix="/crawl-texts", tags=["crawl-texts"])


@router.post("", response_model=CrawlTextResponse, status_code=status.HTTP_201_CREATED)
def create_crawl_text(
    payload: CrawlTextCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permission(UserPermission.DEV)),
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
