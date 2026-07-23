import datetime

from pydantic import BaseModel, Field

from app.core.llm import chat_model
from app.models.crawl_text import CrawlText

MAX_ANALYZE_ATTEMPTS = 3


class AgentParseError(Exception):
    """Raised when the Agent fails to produce a valid structured result after retrying."""


class ProposedScheduleItem(BaseModel):
    title: str = Field(description="일정 제목")
    contents: str = Field(description="일정 내용/설명")
    deadline: datetime.datetime = Field(description="마감 일시 (ISO 8601, 타임존 포함)")


class ProposedScheduleItems(BaseModel):
    items: list[ProposedScheduleItem] = Field(
        description="원문에서 추출한 일정 목록. 일정으로 볼 만한 내용이 없으면 빈 리스트"
    )


def _build_prompt(crawl_text: CrawlText) -> str:
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    return (
        "다음은 Discord 또는 Notion에서 수집한 원문 텍스트입니다. "
        "이 텍스트에서 학생들에게 공유할 일정(과제, 공지, 마감일 등)을 추출해서 "
        "구조화된 형태로 알려주세요. 일정이 아닌 잡담이나 마감일이 없는 내용은 무시하세요. "
        f"오늘 날짜는 {today}(UTC)입니다. 상대적 날짜(예: 다음주 금요일)는 이 기준으로 "
        "계산해서 절대 날짜로 변환해주세요.\n\n"
        f"--- 원문 ---\n{crawl_text.raw_text}"
    )


def analyze_crawl_text(crawl_text: CrawlText) -> list[ProposedScheduleItem]:
    """원문 텍스트를 분석해 제안 항목 목록을 반환. 실패 시 최대 MAX_ANALYZE_ATTEMPTS회 재시도."""

    model = chat_model().with_structured_output(ProposedScheduleItems)
    prompt = _build_prompt(crawl_text)

    last_error: Exception | None = None
    for _ in range(MAX_ANALYZE_ATTEMPTS):
        try:
            result = model.invoke(prompt)
            return result.items
        except Exception as e:  # noqa: BLE001 - broad on purpose, any failure counts as a retry
            last_error = e

    raise AgentParseError(
        f"Failed to parse agent output after {MAX_ANALYZE_ATTEMPTS} attempts"
    ) from last_error
