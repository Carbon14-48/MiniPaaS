from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "build-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    DOCKER_REGISTRY_URL: str = "localhost:5000"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    SECURITY_SCANNER_URL: str = "http://security-scanner:8006"

    class Config:
        env_file = ".env"


settings = Settings()
