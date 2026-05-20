from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVENT_LEDGER_")

    app_name: str = "Event Ledger API"
    database_url: str = "sqlite:///./event_ledger.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
