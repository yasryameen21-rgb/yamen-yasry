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
    firebase_project_id: Optional[str] = "yamensh"
    firebase_private_key_id: Optional[str] = "a574754a9519c5377a974acf903806e5715bd52e"
    firebase_private_key: Optional[str] = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDJLqo9rHk/U2IQ\n8SukscUJihcdk/fQX/AWD7UQDGifBfMlElvpFsMwni/JQYO5il44idR5n1iqTcBG\ngYgtm8x8WYgGvTc2vYYcghfeFH1OpaaoHy0oGh0vSffw7FCxa/pZ13z0nSIymWD4\nbYKRKS4BoRJPOIQJnSfcKC7L0WYWkDyYskZ1+iTvX+xlxJKLjTjyH1af67bcdEOP\n+njYJrd+Gvc+89ee1JhqGhXYmfhAlct/hjirPlWXiTSvElAEs1XJIb3Yy+4DQuEh\nON5C8Q7v43BcW8RndwKZVThtHWHN0vfOehjLNgp53XAdN0RdQKywstX9jA88kDkL\nmTykFP+bAgMBAAECggEAFphtJRwin2AoGtWwxytILA1xvIVf8ewJ37sdOj41NJcg\ne0DCnef2kuv8Bf3xDie3nrYBl99eaqeXjtOsOHh6e6+P6Dcxj65dn69k1YaLmbJf\n3htnoPdoi7p3udFw3AclSRiQv5CJGhHBTbr5ooAeMK9R38qYhH6SztachZEb3DCy\nqrdqSl97SeUZQodX4x1VH3gEL3xsYgVrit7JtQMvoczC/jhcFD3Kr1eXB8sIpjGZ\nsfLJCLx7frZrgPVT10j3h0kyjuSGHjjXUFVpDp5NUkFddoLG7zbaV6iR1JG5QQhJ\n2x7t1wSbd9QrkVnwqlKu2UG1NUR1B232RaB48uMWYQKBgQDoCJhELoFKvxpq8qcJ\nTZfrnWS7e53ht1fZbjO63rzamAANq7sFW2dcClg79yh16H0GjPUpSOwfVrd0u+Yu\nHr1xs79H0zHwvd1Y1GSuLwaBJB4lvRy2ra4uzCg8QZ+79B4o90O+5n67iLgWmvrZ\nTJxPxIemWOXdSwRIGyuIdaaSyQKBgQDd9k3RhpfXSeze4VhkRGKAVg6rHH4Er0MI\n8rJXW87uyZ5f1mRa1T/3llQHHYpBukJG1GhhXUKZeOMEHbaqfZ4CfsOp1xNJwovO\nVAmtNpofaOdQyz7dPlMmKiTvGX2Vney5wv1fRkS6WVWk/y5SA7/7xiWg39URRymS\ncjMXjpVtQwKBgGzia6HDOQT8fMcnK19gPCRi7bxVHBep093Cqx/MGk9x+MRxjAfN\nhslYSWOKbkA2Y0VJrFo9UCC8rsZmznNiFYBf2yk3YD4aut5OfRiIFMNRUZxgDDNl\neVGYmGD+Ypjuy6BpuC7DN0GFvO1OuNxz6P49uXJEUUnxRAcaSOl2XD6RAoGBAMpT\nSQ4T7Pb+2N81dFg5ibxINai+GRT2GVnfuLcu5cr+l9HuYJ33ww5RxpiR0cQmH2Hn\nHpqZ4yp4ah8HYsm4Jb9Kg9qeRWO35a6XJhbxLb4x5qDcE5qixDKGuhIFH1exk+ak\nmkcti1p+MjZrsXJrHqZHMWeagOL2BiwK0w3HF+h3AoGAbzIUjAZMGtv0a23r+bGX\nPiKy/7cObQmMSlwx4VVC4Ijgq/HPPPYvdJ09cYxjhw+wGD+Ia3LYQkkdxIuHBfrO\nF2ZmDCs7YGp6HjweAzue7hbnEbC6BLuviuqB8RtzRORKGoRHSLm07+GkP4yjEhz5\n7aswHFJ9/7ZPIepEE1V5i6w=\n-----END PRIVATE KEY-----\n"
    firebase_client_email: Optional[str] = "firebase-adminsdk-fbsvc@yamensh.iam.gserviceaccount.com"
    firebase_client_id: Optional[str] = "106667331154992179124"
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
