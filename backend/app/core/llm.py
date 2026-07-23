from langchain_openai import ChatOpenAI

from app.core.config import settings


def chat_model(*, temperature: float = 0) -> ChatOpenAI:
    """프록시 서버를 사용하는 공통 채팅 모델 생성 helper입니다."""

    if not settings.has_openai_key:
        raise RuntimeError("PROXY_TOKEN이 .env에 필요합니다.")
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.proxy_token,
        base_url=settings.chat_proxy_url,
        temperature=temperature,
    )
