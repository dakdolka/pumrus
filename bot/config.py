from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    TOKEN: str
    WEB_APP_URL: str
    API_URL: str
    TG_PROXY: str | None = None

    BOT_MODE: Literal["polling", "webhook"] = "polling"
    WEBHOOK_BASE_URL: str | None = None
    WEBHOOK_PATH: str = "/telegram/webhook"
    WEBHOOK_SECRET: str | None = None
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")

    @model_validator(mode="after")
    def validate_webhook_settings(self):
        if not self.WEBHOOK_PATH.startswith("/"):
            raise ValueError("WEBHOOK_PATH must start with '/'")

        if self.BOT_MODE == "webhook":
            if not self.WEBHOOK_BASE_URL:
                raise ValueError("WEBHOOK_BASE_URL is required in webhook mode")
            if not self.WEBHOOK_SECRET:
                raise ValueError("WEBHOOK_SECRET is required in webhook mode")
            if not self.WEBHOOK_BASE_URL.startswith("https://"):
                raise ValueError("WEBHOOK_BASE_URL must use HTTPS")

        return self

    @property
    def webhook_url(self) -> str:
        if not self.WEBHOOK_BASE_URL:
            raise RuntimeError("WEBHOOK_BASE_URL is not configured")
        return f"{self.WEBHOOK_BASE_URL.rstrip('/')}{self.WEBHOOK_PATH}"


settings = Settings()
