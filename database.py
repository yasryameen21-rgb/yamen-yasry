"""
إعدادات قاعدة البيانات والاتصال
"""

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from models import Base


def normalize_database_url(url: str) -> str:
    if not url:
        return "sqlite:///./yamenshat.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


database_url = normalize_database_url(settings.database_url)

try:
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"⚠️ خطأ في إعداد محرك قاعدة البيانات: {str(e)}")
    engine = None
    SessionLocal = None


def init_db():
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ تم إنشاء جميع جداول قاعدة البيانات بنجاح")
        except Exception as e:
            print(f"⚠️ فشل إنشاء الجداول: {str(e)}")
    else:
        print("⚠️ لم يتم إنشاء الجداول لأن المحرك غير متوفر")


def get_db() -> Session:
    if not SessionLocal:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="قاعدة البيانات غير متاحة حالياً. تحقق من DATABASE_URL وإعدادات Render."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def startup_event():
    init_db()
