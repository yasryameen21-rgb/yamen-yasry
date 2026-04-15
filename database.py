"""
إعدادات قاعدة البيانات والاتصال
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from models import Base
import os

# إنشاء محرك قاعدة البيانات
try:
    if settings.database_url.startswith("sqlite"):
        # للـ SQLite نستخدم StaticPool للاختبار
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # لقواعد البيانات الأخرى
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    # إنشاء جلسة
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"⚠️ خطأ في إعداد محرك قاعدة البيانات: {str(e)}")
    engine = None
    SessionLocal = None


def init_db():
    """إنشاء جميع الجداول"""
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ تم إنشاء جميع جداول قاعدة البيانات بنجاح")
        except Exception as e:
            print(f"⚠️ فشل إنشاء الجداول: {str(e)}")
    else:
        print("⚠️ لم يتم إنشاء الجداول لأن المحرك غير متوفر")


def get_db() -> Session:
    """الحصول على جلسة قاعدة البيانات"""
    if not SessionLocal:
        print("⚠️ قاعدة البيانات غير متوفرة")
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# إنشاء الجداول عند بدء التطبيق
def startup_event():
    """حدث بدء التطبيق"""
    init_db()
