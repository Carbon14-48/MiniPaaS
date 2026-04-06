"""
config.py
---------
Configuration centralisée du registry-service.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    registry_url: str = "http://registry:5000"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
