from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    admin_token: str | None = Field(default=None, alias="ADMIN_TOKEN")
    cors_origins: str = Field(
        default=(
            "https://bestgreen.ru,https://www.bestgreen.ru,"
            "http://localhost:3000,http://127.0.0.1:3000"
        ),
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
