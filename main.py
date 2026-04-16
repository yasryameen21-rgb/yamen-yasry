"""
التطبيق الرئيسي للـ API
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os

from config import settings
from database import get_db, startup_event
from security import verify_token, get_current_user
from routes_auth import router as auth_router
from routes_users import router as users_router
from routes_posts import router as posts_router
from routes_notifications import router as notifications_router
from routes_live import router as live_router
from routes_recording import router as recording_router
from routes_firebase import router as firebase_router
from routes_sync import router as sync_router


# ==================== Startup Event ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # Startup
    try:
        startup_event()
        print(f"✅ تم بدء تطبيق {settings.app_name} v{settings.app_version}")
    except Exception as e:
        print(f"⚠️ فشل في حدث بدء التشغيل (startup_event): {str(e)}")
    yield
    # Shutdown
    print("👋 تم إيقاف التطبيق")


# ==================== إنشاء التطبيق ====================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API خادم Yamenshat Pro",
    lifespan=lifespan
)


# ==================== CORS ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== المسارات ====================

# صحة التطبيق
@app.get("/api/health")
async def health_check():
    """فحص صحة التطبيق"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "env": os.getenv("RENDER", "local")
    }


# المسار الرئيسي
@app.get("/")
async def root():
    """المسار الرئيسي"""
    return {
        "message": "Welcome to Yamenshat API!",
        "status": "Running",
        "database": "Available" if os.getenv("DATABASE_URL") else "Missing DATABASE_URL"
    }


# ==================== تسجيل المسارات ====================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(notifications_router)
app.include_router(live_router)
app.include_router(recording_router)
app.include_router(firebase_router)
app.include_router(sync_router)


# ==================== معالجة الأخطاء ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """معالج استثناءات HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": "HTTP_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """معالج الاستثناءات العامة"""
    print(f"❌ خطأ: {str(exc)}")
    payload = {
        "success": False,
        "message": "حدث خطأ في الخادم",
        "error_code": "INTERNAL_SERVER_ERROR"
    }
    if settings.debug:
        payload["detail"] = str(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload
    )


# ==================== Middleware للمصادقة ====================

@app.middleware("http")
async def add_current_user_to_request(request, call_next):
    """إضافة المستخدم الحالي إلى الطلب"""
    authorization = request.headers.get("Authorization")
    
    if authorization:
        try:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                token_data = verify_token(token)
                if token_data:
                    request.state.current_user_id = token_data.user_id
        except Exception:
            pass
    
    response = await call_next(request)
    return response


# ==================== تحديث Dependency ====================

def get_current_user_id(request) -> str:
    """الحصول على معرف المستخدم الحالي من الطلب"""
    return getattr(request.state, "current_user_id", None)


# تحديث المسارات لاستخدام الـ Dependency الجديد
app.dependency_overrides[get_current_user] = get_current_user_id


if __name__ == "__main__":
    import uvicorn
    # الحصول على المنفذ من متغيرات البيئة أو استخدام 8000 افتراضياً
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug
    )
