"""Application configuration. Uses pydantic-settings if available, else defaults."""
import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        app_name: str = "Social Recipe API"
        debug: bool = False
        default_target_language: str = "it"

        class Config:
            env_prefix = "SR_"
            env_file = ".env"

    def get_settings() -> Settings:
        return Settings()
except ImportError:
    # Fallback when pydantic_settings not installed
    class Settings:
        app_name: str = "Social Recipe API"
        debug: bool = False
        default_target_language: str = "it"

    def get_settings() -> Settings:
        return Settings()
