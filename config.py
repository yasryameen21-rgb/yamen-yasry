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
# القيمة الافتراضية هي 'development'
APP_ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    """إعدادات التطبيق"""
    
    # معلومات التطبيق
    app_name: str = "Yamenshat API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # قاعدة البيانات
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./yamenshat.db")
    
    # JWT والمصادقة
    secret_key: str = "your-secret-key-change-in-production"
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
    
   # CORS - السماح فقط بالنطاقات الموثوقة
allowed_origins: List[str] = (
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://yasryameen21-rgb.github.io", # رابط GitHub Pages الخاص بك
    "https://yamen-chat-web-frontend.onrender.com", # إذا كنت نشرت الواجهة على Render أيضاً
    "https://yamen-yasry-backend.onrender.com" # رابط السيرفر نفسه
)


    
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
