import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google Calendar OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REFRESH_TOKEN: Optional[str] = None
    GOOGLE_CALENDAR_ID: str = "primary"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "*"

    # Calendar Rules
    BUSINESS_HOURS_START: int = 9   # 9 AM
    BUSINESS_HOURS_END: int = 17    # 5 PM
    MEETING_DURATION_MINUTES: int = 30
    TIMEZONE_DEFAULT: str = "America/New_York"

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated allowed origins."""
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def has_google_credentials(self) -> bool:
        """Check if all required Google OAuth2 credentials are configured."""
        return bool(
            self.GOOGLE_CLIENT_ID
            and self.GOOGLE_CLIENT_SECRET
            and self.GOOGLE_REFRESH_TOKEN
            and not self.GOOGLE_CLIENT_ID.startswith("123456789012-mock")
        )


settings = Settings()
