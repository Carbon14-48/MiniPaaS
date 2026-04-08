from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "security-scanner"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"

    DOCKER_SOCKET_PATH: str = "/var/run/docker.sock"

    TRIVY_PATH: str = "/usr/local/bin/trivy"
    COSIGN_PATH: str = "/usr/local/bin/cosign"
    YARA_RULES_DIR: str = "/rules"
    CLAMAV_DB_PATH: str = "/var/lib/clamav"

    SCANNER_MAX_TIMEOUT: int = 300
    BLOCK_ON_HIGH_CVES: bool = True
    BLOCK_ON_MALWARE: bool = True
    BLOCK_ON_SECRETS: bool = True
    BLOCK_ON_ROOT_USER: bool = True

    COSIGN_KEY_PATH: str = "/keys/cosign.key"
    COSIGN_KEY_PASSWORD: str = ""
    COSIGN_KEYLESS: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
