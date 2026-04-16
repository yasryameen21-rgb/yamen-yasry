"""
مسارات المستخدمين
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, UserSettings
from schemas import UserResponse, UserUpdate, UserDetailResponse, UserSettingsResponse, UserSettingsUpdate
from security import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على بيانات المستخدم الحالي
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
    
    return user


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    الحصول على بيانات مستخدم معين
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return user


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    الحصول على قائمة المستخدمين
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحديث بيانات المستخدم الحالي
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
    
    # تحديث البيانات
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/friends/{friend_id}")
async def add_friend(
    friend_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إضافة صديق
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    
    if not user or not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    if friend not in user.friends:
        user.friends.append(friend)
        db.commit()
    
    return {"success": True, "message": "تم إضافة الصديق بنجاح"}


@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إزالة صديق
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    
    if not user or not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    if friend in user.friends:
        user.friends.remove(friend)
        db.commit()
    
    return {"success": True, "message": "تم إزالة الصديق بنجاح"}


@router.get("/{user_id}/friends", response_model=List[UserResponse])
async def get_user_friends(user_id: str, db: Session = Depends(get_db)):
    """
    الحصول على قائمة أصدقاء المستخدم
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    return user.friends


@router.get("/settings/me", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على إعدادات المستخدم
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user_id
    ).first()
    
    if not settings:
        # إنشاء إعدادات افتراضية
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.put("/settings/me", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحديث إعدادات المستخدم
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user_id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user_id)
        db.add(settings)
    
    # تحديث البيانات
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    
    return settings


@router.post("/ban/{user_id}")
async def ban_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    حظر مستخدم (للمشرفين فقط)
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    admin = db.query(User).filter(User.id == current_user_id).first()
    if not admin or admin.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحيات كافية"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    user.is_banned = True
    db.commit()
    
    return {"success": True, "message": "تم حظر المستخدم بنجاح"}


@router.post("/unban/{user_id}")
async def unban_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إلغاء حظر مستخدم (للمشرفين فقط)
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    admin = db.query(User).filter(User.id == current_user_id).first()
    if not admin or admin.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحيات كافية"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    user.is_banned = False
    db.commit()
    
    return {"success": True, "message": "تم إلغاء حظر المستخدم بنجاح"}
