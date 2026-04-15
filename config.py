"""
ملف الإعدادات الرئيسي للتطبيق
يتحكم في جميع متغيرات البيئة والإعدادات الأساسية
يدعم التحميل التلقائي من ملفات .env المختلفة بناءً على البيئة
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache


# تحديد البيئة الحالية (development, production, testing)
# القيمة الافتراضية هي 'production' للربط السحابي
APP_ENV = os.getenv("APP_ENV", "production")


class Settings(BaseSettings):
    """إعدادات التطبيق"""
    
    # معلومات التطبيق
    app_name: str = "Yamenshat API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # قاعدة البيانات - تم تحديثها لرابط Render
    database_url: str = os.getenv("DATABASE_URL","postgresql://yamenshat_db_user:K0v4262p6Z9v095u6f873arhot0@dpg-d7bsqu117lss73arhot0-a.oregon-postgres.render.com/yamenshat_dbresql://yamenshat_user:oEDMUD2CnteWuPGtpJ7yYTgeuQyJyXzo@dpg-d7bsqu117lss73arhot0-a/yamenshat_db?sslmode=require")
    
    # JWT والمصادقة
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Firebase
    firebase_project_id: Optional[str] = None
    firebase_private_key_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    firebase_client_id: Optional[str] = None
    firebase_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://yamen-yasry-backend.onrender.com",
    ]
    
    class Config:
        # تحميل ملف .env المناسب للبيئة
        env_file = f".env.{APP_ENV}" if APP_ENV else ".env"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings():
    """الحصول على نسخة من الإعدادات مع التخزين المؤقت للأداء"""
    return Settings()


# تصدير الإعدادات للاستخدام في التطبيق
settings = get_settings()
print(f"--- Loaded Settings for Environment: {APP_ENV} (Debug: {settings.debug}) ---")
