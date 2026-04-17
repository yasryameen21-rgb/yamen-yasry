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
    ResetPassword, VerifyEmail, Token, OtpRequest, OtpVerify,
    OnboardingRegistrationRequest, OnboardingAuthResponse, OnboardingProfileResponse
)
from security import (
    verify_password, get_password_hash, create_tokens, verify_token, get_current_user
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


@router.post("/register-profile", response_model=OnboardingAuthResponse)
async def register_profile(data: OnboardingRegistrationRequest, db: Session = Depends(get_db)):
    """
    تسجيل سريع من شاشة إنشاء الحساب الجديدة بالموبايل
    """
    display_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()

    normalized_email = None
    normalized_phone = None

    if data.contact_method == "email":
        normalized_email = data.contact.strip().lower()
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مسجل بالفعل"
            )
    else:
        normalized_phone = data.contact.strip()
        generated_local_email = f"{normalized_phone}@familyhub.local"
        existing_phone = db.query(User).filter(User.phone_number == normalized_phone).first()
        existing_email = db.query(User).filter(User.email == generated_local_email).first()
        if existing_phone or existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رقم الجوال مسجل بالفعل"
            )
        normalized_email = generated_local_email

    temp_secret_suffix = (normalized_phone or normalized_email.split('@')[0])[-6:]
    generated_password = get_password_hash(f"FH@{temp_secret_suffix}")

    new_user = User(
        name=display_name,
        email=normalized_email,
        password_hash=generated_password,
        phone_number=normalized_phone,
        is_verified=(data.contact_method == "phone")
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    tokens = create_tokens(
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role.value
    )

    profile = OnboardingProfileResponse(
        id=f"profile_{new_user.id}",
        user_id=new_user.id,
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        display_name=display_name,
        date_of_birth=data.date_of_birth,
        contact_method=data.contact_method,
        contact=data.contact.strip(),
        created_at=datetime.utcnow()
    )

    return OnboardingAuthResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user_id=new_user.id,
        display_name=display_name,
        email=(normalized_email if data.contact_method == "email" else None),
        phone_number=normalized_phone,
        profile=profile
    )


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
    current_user_id: str = Depends(get_current_user),
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


# محاكاة بسيطة للـ OTP (في الإنتاج يجب ربطه بخدمة SMS أو SMTP)
# ملاحظة: هذا للتوضيح والربط، في الإنتاج يجب استخدام Redis أو قاعدة بيانات لتخزين الرموز
temp_otp_storage = {}

@router.post("/send-otp")
async def send_otp(request: OtpRequest, db: Session = Depends(get_db)):
    """
    إرسال رمز التحقق (محاكاة)
    """
    identifier = request.phone_number or request.email
    if not identifier:
        raise HTTPException(status_code=400, detail="يجب توفير رقم الهاتف أو البريد الإلكتروني")
    
    # توليد رمز ثابت للتجربة أو عشوائي
    otp = "123456" 
    temp_otp_storage[identifier] = otp
    
    print(f"--- OTP for {identifier}: {otp} ---")
    
    return {"success": True, "message": f"تم إرسال الرمز إلى {identifier}"}

@router.post("/login-phone", response_model=Token)
async def login_phone(data: OtpVerify, db: Session = Depends(get_db)):
    """
    تسجيل الدخول برقم الهاتف
    """
    if not data.phone_number or data.otp_code != temp_otp_storage.get(data.phone_number):
        raise HTTPException(status_code=401, detail="رمز التحقق غير صحيح")
    
    # البحث عن المستخدم برقم الهاتف أو إنشاؤه
    user = db.query(User).filter(User.phone_number == data.phone_number).first()
    if not user:
        # إنشاء مستخدم جديد تلقائياً عند الدخول لأول مرة بالهاتف
        user = User(
            name=f"User_{data.phone_number[-4:]}",
            email=f"{data.phone_number}@familyhub.local",
            password_hash=get_password_hash("default_pass_otp"),
            phone_number=data.phone_number,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return create_tokens(user_id=user.id, email=user.email, role=user.role.value)

@router.post("/login-email", response_model=Token)
async def login_email(data: OtpVerify, db: Session = Depends(get_db)):
    """
    تسجيل الدخول بالبريد الإلكتروني (OTP)
    """
    if not data.email or data.otp_code != temp_otp_storage.get(data.email):
        raise HTTPException(status_code=401, detail="رمز التحقق غير صحيح")
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        user = User(
            name=data.email.split('@')[0],
            email=data.email,
            password_hash=get_password_hash("default_pass_otp"),
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return create_tokens(user_id=user.id, email=user.email, role=user.role.value)
