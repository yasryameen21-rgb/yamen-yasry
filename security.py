"""
نظام الأمان والمصادقة JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Header
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from config import settings

# إعدادات التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# نماذج JWT
class TokenData(BaseModel):
    """بيانات التوكن"""
    user_id: str
    email: str
    role: str = "user"


class Token(BaseModel):
    """نموذج التوكن"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """طلب تحديث التوكن"""
    refresh_token: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """الحصول على تجزئة كلمة المرور"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """إنشاء توكن الوصول"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """إنشاء توكن التحديث"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """التحقق من صحة التوكن"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email, role=role)
    
    except JWTError:
        return None


def create_tokens(user_id: str, email: str, role: str = "user") -> Token:
    """إنشاء توكنات الوصول والتحديث"""
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    
    access_token = create_access_token(
        data={"sub": user_id, "email": email, "role": role},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user_id, "email": email}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


async def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization")
):
    """الحصول على المستخدم الحالي من التوكن"""
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        token_data = verify_token(token)
        if not token_data:
            return None
        
        return token_data.user_id
    
    except Exception:
        return None
