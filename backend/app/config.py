from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

    # API security
    api_secret_key: str

    # Instagram ingestion
    insta_username: str
    insta_password: str
    instagrapi_session_file: str

    # Substack ingestion
    substack_rss_url: str

    # AI location inference
    anthropic_api_key: str

    # CORS
    frontend_origin: str

    # Optional: Instagram Graph API fallback
    instagram_graph_api_token: str = ""

    # Optional: polling intervals (minutes)
    instagram_poll_interval_minutes: int = 60
    substack_poll_interval_minutes: int = 60

    # Optional: SMTP for session-expiry alerts
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Logging
    log_level: str = "INFO"
    environment: str = "production"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got {v!r}")
        return upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got {v!r}")
        return lower


settings = Settings()
