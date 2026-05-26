from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Single container: use SQLite for simplicity
    data_dir: str = "/data"
    database_url: str = f"sqlite+aiosqlite:///{os.getenv('DATA_DIR', '/data')}/fauxx.db"
    # Redis not needed for single-container, use in-memory for caching
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
