from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    admin_token: str | None = Field(default=None, alias="ADMIN_TOKEN")
    backend_internal_token: str | None = Field(
        default=None,
        alias="BACKEND_INTERNAL_TOKEN",
    )
    allow_insecure_admin: bool = Field(
        default=False,
        alias="ALLOW_INSECURE_ADMIN",
    )
    media_root: Path = Field(
        default=BASE_DIR.parent / "media",
        alias="MEDIA_ROOT",
    )
    media_max_bytes: int = Field(
        default=8 * 1024 * 1024,
        alias="MEDIA_MAX_BYTES",
    )
    payment_mode: str = Field(default="disabled", alias="PAYMENT_MODE")
    telegram_bot_token: str | None = Field(
        default=None,
        alias="TELEGRAM_BOT_TOKEN",
    )
    yookassa_shop_id: str | None = Field(
        default=None,
        alias="YOOKASSA_SHOP_ID",
    )
    yookassa_secret_key: str | None = Field(
        default=None,
        alias="YOOKASSA_SECRET_KEY",
    )
    payment_return_url: str = Field(
        default="https://bestgreen.ru/payment/return",
        alias="PAYMENT_RETURN_URL",
    )
    payment_terms_url: str | None = Field(
        default=None,
        alias="PAYMENT_TERMS_URL",
    )
    payment_support_url: str | None = Field(
        default=None,
        alias="PAYMENT_SUPPORT_URL",
    )
    telegram_init_data_max_age: int = Field(
        default=86_400,
        alias="TELEGRAM_INIT_DATA_MAX_AGE",
    )
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

    @property
    def payments_enabled(self) -> bool:
        return (
            self.payment_mode == "yookassa"
            and bool(self.yookassa_shop_id)
            and bool(self.yookassa_secret_key)
        )


settings = Settings()
