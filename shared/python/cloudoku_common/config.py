from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    APP_NAME: str = "cloudoku-service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: list[str] = ["*"]

    DATABASE_URL: str = "postgresql://cloudoku:cloudoku@postgres:5432/cloudoku"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        env_file = ".env"
