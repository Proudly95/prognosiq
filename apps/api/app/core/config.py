from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_enconding="utf-8")

    database_url: str = "postgresql+psycopg://prognosiq:prognosiq@localhost:5432/prognosiq"


settings = Settings()
