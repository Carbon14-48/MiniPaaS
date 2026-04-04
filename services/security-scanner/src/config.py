from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "security-scanner"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    SONARQUBE_URL: str = "http://sonarqube:9000"
    TRIVY_CACHE_DIR: str = "/tmp/trivy-cache"

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    class Config:
        env_file = ".env"


settings = Settings()
