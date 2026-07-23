from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://katecam:katecam@localhost:5432/katecam"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 90
    rate_limit_enabled: bool = True

    proxy_token: str = ""
    chat_proxy_url: str = ""
    openai_model: str = ""

    @property
    def has_openai_key(self) -> bool:
        return bool(self.proxy_token)


settings = Settings()
