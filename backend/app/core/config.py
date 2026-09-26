import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):

    app_name: str = Field(default="Hurricane Week Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        APP_NAME=os.getenv("APP_NAME", "Hurricane Week Backend"),
        APP_ENV=os.getenv("APP_ENV", "development"),
        APP_DEBUG=os.getenv("APP_DEBUG", "true").lower() == "true",
        API_PREFIX=os.getenv("API_PREFIX", "/api"),
        ALLOWED_ORIGINS=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000"),
    )
