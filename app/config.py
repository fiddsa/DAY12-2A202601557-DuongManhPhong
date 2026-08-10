"""CP1 — Cấu hình theo 12-Factor."""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    port: int = 8000
    agent_api_key: str
    redis_url: str = 'redis://localhost:6379/0'
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    log_level: str = 'INFO'

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
