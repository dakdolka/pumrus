from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(BASE_DIR)

class Settings(BaseSettings):
    host: str
    user: str
    password: str
    db: str  # имя базы данных
    port: str
    
    
    @property
    def db_url(self):
        return f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_file = f'{os.path.join(BASE_DIR.parent, ".env")}'

settings = Settings()