from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "monitoring-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    PROMETHEUS_URL: str = "http://prometheus:9090"
    LOKI_URL: str = "http://loki:3100"

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        env_file = ".env"


settings = Settings()
