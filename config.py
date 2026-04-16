"""
ملف الإعدادات الرئيسي للتطبيق
يتحكم في جميع متغيرات البيئة والإعدادات الأساسية
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache

APP_ENV = os.getenv("APP_ENV", os.getenv("ENV", "production"))


def _build_allowed_origins() -> List[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000,https://yamen-yasry-backend.onrender.com"
    )
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseSettings):
    app_name: str = os.getenv("APP_NAME", "Yamenshat API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # قاعدة البيانات: نستخدم قيمة البيئة إن وُجدت، وإلا SQLite محلياً لتجنب انهيار الخدمة
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./yamenshat.db")

    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    firebase_private_key_id: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = os.getenv("FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = os.getenv("FIREBASE_CLIENT_ID")
    firebase_auth_uri: str = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    firebase_token_uri: str = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")

    allowed_origins: List[str] = _build_allowed_origins()

    class Config:
        env_file = f".env.{APP_ENV}" if APP_ENV else ".env"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
print(f"--- Loaded Settings for Environment: {APP_ENV} (Debug: {settings.debug}) ---")
