from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # = app/api -where .env actually lives


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://prognosiq:prognosiq@localhost:5432/prognosiq"
    database_url_test: str = "postgresql+psycopg://prognosiq:prognosiq@localhost:5432/prognosiq"
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


settings = Settings()
