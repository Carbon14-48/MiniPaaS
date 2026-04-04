from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "api-gateway"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    APP_MANAGEMENT_SERVICE_URL: str = "http://app-management:8002"
    BUILD_SERVICE_URL: str = "http://build-service:8003"
    DEPLOYMENT_SERVICE_URL: str = "http://deployment-service:8004"
    MONITORING_SERVICE_URL: str = "http://monitoring-service:8005"
    SECURITY_SCANNER_URL: str = "http://security-scanner:8006"

    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
