import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "super_secret_recoverai_key_change_in_production_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database (Default: SQLite zero-setup file db)
    DATABASE_URL: str = "sqlite+aiosqlite:///./recoverai.db"

    # Redis (Optional in local dev)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Gemini API Key (Free Tier Supported)
    GEMINI_API_KEY: str = ""

    # OpenAI API Key (Optional)
    OPENAI_API_KEY: str = ""

    # Twilio SMS (Disabled / Not Required)
    ENABLE_SMS_ALERTS: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def effective_gemini_api_key(self) -> str:
        """Returns environment variable GEMINI_API_KEY from process environment or settings."""
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_key and not env_key.startswith("your_"):
            return env_key
        if self.GEMINI_API_KEY and not self.GEMINI_API_KEY.startswith("your_"):
            return self.GEMINI_API_KEY
        return ""


settings = Settings()
