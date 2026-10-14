from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_enconding="utf-8")

    database_url: str = "postgresql+psycopg://prognosiq:prognosiq@localhost:5432/prognosiq"
    database_url_test: str = (
        "postgresql+psycopg://prognosiq:prognosiq@localhost:5432/prognosiq_test"
    )


settings = Settings()
