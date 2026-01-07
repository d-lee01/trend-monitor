from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # External API Keys
    reddit_client_id: str
    reddit_client_secret: str
    youtube_api_key: str
    similarweb_api_key: str
    anthropic_api_key: str

    # Application
    app_name: str = "trend-monitor"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
