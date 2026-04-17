"""
ملف الإعدادات الرئيسي للتطبيق
يتحكم في متغيرات البيئة والإعدادات الأساسية
"""

from functools import lru_cache
from typing import List, Optional
import json
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


APP_ENV = os.getenv("APP_ENV", "production")

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://yamen-yasry-backend.onrender.com",
]


class Settings(BaseSettings):
    """إعدادات التطبيق"""

    model_config = SettingsConfigDict(
        env_file=f".env.{APP_ENV}" if APP_ENV else ".env",
        case_sensitive=False,
        extra="allow",
    )

    # معلومات التطبيق
    app_name: str = Field(default="Yamenshat API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # قاعدة البيانات
    database_url: str = Field(default="sqlite:///./yamenshat.db")

    # JWT والمصادقة
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # Firebase
    firebase_project_id: Optional[str] = Field(default=None)
    firebase_private_key_id: Optional[str] = Field(default=None)
    firebase_private_key: Optional[str] = Field(default=None)
    firebase_client_email: Optional[str] = Field(default=None)
    firebase_client_id: Optional[str] = Field(default=None)
    firebase_auth_uri: str = Field(default="https://accounts.google.com/o/oauth2/auth")
    firebase_token_uri: str = Field(default="https://oauth2.googleapis.com/token")

    # CORS
    allowed_origins: List[str] = Field(default_factory=lambda: DEFAULT_ALLOWED_ORIGINS.copy())

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        if value is None:
            return "sqlite:///./yamenshat.db"
        if isinstance(value, str) and not value.strip():
            return "sqlite:///./yamenshat.db"
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if value is None or value == "":
            return DEFAULT_ALLOWED_ORIGINS.copy()

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return DEFAULT_ALLOWED_ORIGINS.copy()

            if raw_value.startswith("["):
                try:
                    parsed = json.loads(raw_value)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass

            return [item.strip() for item in raw_value.split(",") if item.strip()]

        return DEFAULT_ALLOWED_ORIGINS.copy()

    @field_validator("firebase_private_key", mode="before")
    @classmethod
    def normalize_private_key(cls, value):
        if isinstance(value, str) and value:
            return value.replace("\\n", "\n")
        return value


@lru_cache()
def get_settings():
    """الحصول على نسخة من الإعدادات مع التخزين المؤقت"""
    return Settings()


settings = get_settings()
print(f"--- Loaded Settings for Environment: {APP_ENV} (Debug: {settings.debug}) ---")
