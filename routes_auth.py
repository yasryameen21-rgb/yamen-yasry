"""
مسارات المصادقة والتسجيل
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User
from schemas import (
    UserRegister, UserLogin, UserResponse, ChangePassword,
    ResetPassword, VerifyEmail, Token
)
from security import (
    verify_password, get_password_hash, create_tokens, verify_token
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    تسجيل مستخدم جديد
    """
    # التحقق من عدم وجود بريد إلكتروني مسجل
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مسجل بالفعل"
        )
    
    # إنشاء مستخدم جديد
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        phone_number=user_data.phone_number,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    تسجيل الدخول
    """
    # البحث عن المستخدم
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الدخول غير صحيحة"
        )
    
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تم حظر هذا الحساب"
        )
    
    # تحديث آخر تسجيل دخول
    user.last_login = datetime.utcnow()
    db.commit()
    
    # إنشاء التوكنات
    tokens = create_tokens(
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )
    
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(request: dict, db: Session = Depends(get_db)):
    """
    تحديث التوكن
    """
    refresh_token = request.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توكن التحديث مطلوب"
        )
    
    # التحقق من التوكن
    token_data = verify_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توكن التحديث غير صحيح"
        )
    
    # الحصول على المستخدم
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # إنشاء توكنات جديدة
    tokens = create_tokens(
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )
    
    return tokens


@router.post("/change-password")
async def change_password(
    data: ChangePassword,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    تغيير كلمة المرور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # التحقق من كلمة المرور القديمة
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور القديمة غير صحيحة"
        )
    
    # تحديث كلمة المرور
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    
    return {"success": True, "message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """
    إعادة تعيين كلمة المرور (نسيت كلمة المرور)
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="البريد الإلكتروني غير موجود"
        )
    
    # في التطبيق الحقيقي، يتم إرسال بريد إلكتروني برابط إعادة التعيين
    # هنا نقوم بإنشاء كلمة مرور مؤقتة
    temp_password = "TempPassword123!"
    user.password_hash = get_password_hash(temp_password)
    db.commit()
    
    return {
        "success": True,
        "message": "تم إرسال تعليمات إعادة التعيين إلى بريدك الإلكتروني"
    }


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmail,
    db: Session = Depends(get_db)
):
    """
    التحقق من البريد الإلكتروني
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # في التطبيق الحقيقي، يتم التحقق من الكود المرسل للبريد الإلكتروني
    # هنا نقبل أي كود لأغراض التطوير
    if data.verification_code:
        user.is_verified = True
        db.commit()
        return {"success": True, "message": "تم التحقق من البريد الإلكتروني بنجاح"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="كود التحقق غير صحيح"
    )


@router.post("/logout")
async def logout(current_user_id: str = None):
    """
    تسجيل الخروج
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    # في التطبيق الحقيقي، يتم إضافة التوكن إلى قائمة سوداء
    return {"success": True, "message": "تم تسجيل الخروج بنجاح"}
