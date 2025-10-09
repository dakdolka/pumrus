from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    TOKEN: str
    WEB_APP_URL: str

    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env')

settings = Settings()