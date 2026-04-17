"""
مسارات المصادقة والتسجيل
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    ChangePassword,
    OnboardingAuthResponse,
    OnboardingProfileResponse,
    OnboardingRegistrationRequest,
    OtpRequest,
    OtpVerify,
    ResetPassword,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    VerifyEmail,
)
from security import (
    create_tokens,
    get_current_user,
    get_password_hash,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().replace(" ", "").replace("-", "")
    return normalized or None


def _resolve_otp_identifier(phone_number: str | None = None, email: str | None = None) -> str:
    normalized_phone = _normalize_phone(phone_number)
    normalized_email = _normalize_email(email)
    identifier = normalized_phone or normalized_email
    if not identifier:
        raise HTTPException(status_code=400, detail="يجب توفير رقم الهاتف أو البريد الإلكتروني")
    return identifier


def _assert_valid_otp(identifier: str, otp_code: str | None):
    if not otp_code:
        raise HTTPException(status_code=400, detail="رمز التحقق مطلوب")

    cached_code = temp_otp_storage.get(identifier)
    if otp_code != cached_code:
        raise HTTPException(status_code=401, detail="رمز التحقق غير صحيح")


def _clear_otp(identifier: str):
    temp_otp_storage.pop(identifier, None)


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    تسجيل مستخدم جديد
    """
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مسجل بالفعل"
        )

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
    تسجيل حساب جديد مع كلمة مرور ورمز تحقق إلزامي
    """
    display_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()

    normalized_email = None
    normalized_phone = None

    if data.contact_method == "email":
        normalized_email = _normalize_email(data.contact)
        if not normalized_email:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني غير صالح")

        _assert_valid_otp(normalized_email, data.verification_code)

        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مسجل بالفعل"
            )
    else:
        normalized_phone = _normalize_phone(data.contact)
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="رقم الجوال غير صالح")

        _assert_valid_otp(normalized_phone, data.verification_code)

        generated_local_email = f"{normalized_phone}@familyhub.local"
        existing_phone = db.query(User).filter(User.phone_number == normalized_phone).first()
        existing_email = db.query(User).filter(User.email == generated_local_email).first()
        if existing_phone or existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رقم الجوال مسجل بالفعل"
            )
        normalized_email = generated_local_email

    new_user = User(
        name=display_name,
        email=normalized_email,
        password_hash=get_password_hash(data.password),
        phone_number=normalized_phone,
        is_verified=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    _clear_otp(normalized_phone or normalized_email)

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
        contact=(normalized_phone or normalized_email),
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
    normalized_email = _normalize_email(credentials.email)
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الدخول غير صحيحة"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لازم تفعّل الحساب برمز التحقق أولاً"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تم حظر هذا الحساب"
        )

    user.last_login = datetime.utcnow()
    db.commit()

    return create_tokens(
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: dict, db: Session = Depends(get_db)):
    """
    تحديث التوكن
    """
    refresh_token_value = request.get("refresh_token")

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توكن التحديث مطلوب"
        )

    token_data = verify_token(refresh_token_value)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توكن التحديث غير صحيح"
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )

    return create_tokens(
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )


@router.post("/change-password")
async def change_password(
    data: ChangePassword,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور القديمة غير صحيحة"
        )

    user.password_hash = get_password_hash(data.new_password)
    db.commit()

    return {"success": True, "message": "تم تغيير كلمة المرور بنجاح"}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == _normalize_email(data.email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="البريد الإلكتروني غير موجود"
        )

    temp_password = "TempPassword123!"
    user.password_hash = get_password_hash(temp_password)
    db.commit()

    return {
        "success": True,
        "message": "تم إرسال تعليمات إعادة التعيين إلى بريدك الإلكتروني"
    }


@router.post("/verify-email")
async def verify_email(data: VerifyEmail, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(data.email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )

    _assert_valid_otp(normalized_email, data.verification_code)
    user.is_verified = True
    db.commit()
    _clear_otp(normalized_email)
    return {"success": True, "message": "تم التحقق من البريد الإلكتروني بنجاح"}


@router.post("/logout")
async def logout(current_user_id: str = None):
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )

    return {"success": True, "message": "تم تسجيل الخروج بنجاح"}


# محاكاة بسيطة للـ OTP (في الإنتاج يجب ربطه بخدمة SMS أو SMTP)
temp_otp_storage: dict[str, str] = {}


@router.post("/send-otp")
async def send_otp(request: OtpRequest, db: Session = Depends(get_db)):
    """
    إرسال رمز التحقق (محاكاة)
    """
    identifier = _resolve_otp_identifier(request.phone_number, request.email)
    otp = "123456"
    temp_otp_storage[identifier] = otp

    print(f"--- OTP for {identifier}: {otp} ---")

    return {"success": True, "message": f"تم إرسال الرمز إلى {identifier}"}


@router.post("/login-phone", response_model=Token)
async def login_phone(data: OtpVerify, db: Session = Depends(get_db)):
    """
    تسجيل الدخول برقم الهاتف عبر OTP لمستخدم موجود
    """
    normalized_phone = _normalize_phone(data.phone_number)
    if not normalized_phone:
        raise HTTPException(status_code=400, detail="رقم الجوال مطلوب")

    _assert_valid_otp(normalized_phone, data.otp_code)

    user = db.query(User).filter(User.phone_number == normalized_phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="الحساب غير موجود، أنشئ حساباً أولاً")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="الحساب غير مفعّل بعد")

    user.last_login = datetime.utcnow()
    db.commit()
    _clear_otp(normalized_phone)
    return create_tokens(user_id=user.id, email=user.email, role=user.role.value)


@router.post("/login-email", response_model=Token)
async def login_email(data: OtpVerify, db: Session = Depends(get_db)):
    """
    تسجيل الدخول بالبريد الإلكتروني عبر OTP لمستخدم موجود
    """
    normalized_email = _normalize_email(data.email)
    if not normalized_email:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مطلوب")

    _assert_valid_otp(normalized_email, data.otp_code)

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="الحساب غير موجود، أنشئ حساباً أولاً")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="الحساب غير مفعّل بعد")

    user.last_login = datetime.utcnow()
    db.commit()
    _clear_otp(normalized_email)
    return create_tokens(user_id=user.id, email=user.email, role=user.role.value)
