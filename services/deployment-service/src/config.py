from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "deployment-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]

    KUBECONFIG_PATH: str = "/root/.kube/config"
    CLOUDOKU_DOMAIN: str = "cloudoku.app"

    class Config:
        extra = "ignore"
        env_file = ".env"


settings = Settings()
