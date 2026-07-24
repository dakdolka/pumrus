from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    admin_token: str | None = Field(default=None, alias="ADMIN_TOKEN")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
