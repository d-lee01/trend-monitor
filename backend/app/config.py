from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: Optional[str] = None

    # JWT Authentication
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # External API Keys
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    youtube_api_key: Optional[str] = None
    similarweb_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Application
    app_name: str = "trend-monitor"
    app_version: str = "1.0.0"
    debug: bool = False

    # CORS
    cors_origins: str = "http://localhost:3000"  # Comma-separated list

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
