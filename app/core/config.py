from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./xiaoman-dev.db"
    app_secret_key: str = "dev-only-change-me"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me-before-deploy"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
