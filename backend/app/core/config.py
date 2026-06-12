from functools import lru_cache
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TALON"
    environment: str = "development"
    database_url: str = "sqlite:///./talon_local.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    default_coach_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    frontend_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    coach_display_name: str = "TALON Coach"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    recall_api_key: str | None = None
    recall_webhook_secret: str | None = None
    recall_region: str = "us-east-1"
    public_backend_url: str = "http://localhost:8000"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_calendar_scopes: str = "https://www.googleapis.com/auth/calendar"
    frontend_url: str = "http://localhost:5173"
    token_encryption_key: str | None = None
    zoom_account_id: str | None = None
    zoom_client_id: str | None = None
    zoom_client_secret: str | None = None
    zoom_user_id: str = "me"
    teams_access_token: str | None = None
    microsoft_tenant_id: str | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    teams_user_id: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from_email)

    @property
    def google_scopes(self) -> list[str]:
        return [scope.strip() for scope in self.google_calendar_scopes.split(",") if scope.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
