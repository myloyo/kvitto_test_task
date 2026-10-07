from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite:///./payments.db"

    webhook_secret: str = "change-me"
    # По умолчанию выкл.: иначе каждый curl к вебхуку нужен с HMAC.
    webhook_verify_signature: bool = False

    bank_base_url: str = "https://bank.local"
    bank_retry_attempts: int = 3
    bank_retry_base_delay: float = 0.2
    bank_timeout: float = 5.0
    # По умолчанию выкл.: тесты и сдача не ходят в сеть.
    bank_confirm_on_webhook: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
