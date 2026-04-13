"""
مسارات الإشعارات
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Notification, User
from schemas import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إنشاء إشعار جديد
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    # التحقق من وجود المستخدم
    user = db.query(User).filter(User.id == notification_data.related_id or current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # إنشاء الإشعار
    new_notification = Notification(
        user_id=notification_data.related_id or current_user_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        related_id=notification_data.related_id,
        is_read=False
    )
    
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    return new_notification


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    current_user_id: str = None,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    الحصول على إشعارات المستخدم
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    query = db.query(Notification).filter(Notification.user_id == current_user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return notifications


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    الحصول على إشعار معين
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الإشعار غير موجود"
        )
    
    if notification.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك الوصول إلى هذا الإشعار"
        )
    
    return notification


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    تحديد الإشعار كمقروء
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الإشعار غير موجود"
        )
    
    if notification.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك الوصول إلى هذا الإشعار"
        )
    
    notification.is_read = True
    db.commit()
    
    return {"success": True, "message": "تم تحديد الإشعار كمقروء"}


@router.put("/read-all")
async def mark_all_as_read(
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    تحديد جميع الإشعارات كمقروءة
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    db.query(Notification).filter(
        Notification.user_id == current_user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"success": True, "message": "تم تحديد جميع الإشعارات كمقروءة"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    حذف إشعار
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الإشعار غير موجود"
        )
    
    if notification.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك حذف هذا الإشعار"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"success": True, "message": "تم حذف الإشعار بنجاح"}


@router.get("/count/unread")
async def get_unread_count(
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    الحصول على عدد الإشعارات غير المقروءة
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user_id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": unread_count}


# ==================== إرسال الإشعارات ====================

@router.post("/send/like")
async def send_like_notification(
    post_id: str,
    post_author_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعار إعجاب
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    
    notification = Notification(
        user_id=post_author_id,
        title="إعجاب جديد",
        message=f"أعجب {user.name} بمنشورك",
        notification_type="like",
        related_id=post_id,
        is_read=False
    )
    
    db.add(notification)
    db.commit()
    
    return {"success": True, "message": "تم إرسال الإشعار بنجاح"}


@router.post("/send/comment")
async def send_comment_notification(
    post_id: str,
    post_author_id: str,
    comment_text: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعار تعليق
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    
    notification = Notification(
        user_id=post_author_id,
        title="تعليق جديد",
        message=f"علق {user.name}: {comment_text[:50]}...",
        notification_type="comment",
        related_id=post_id,
        is_read=False
    )
    
    db.add(notification)
    db.commit()
    
    return {"success": True, "message": "تم إرسال الإشعار بنجاح"}


@router.post("/send/task-assignment")
async def send_task_assignment_notification(
    task_id: str,
    assigned_to_id: str,
    task_title: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعار تعيين مهمة
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    notification = Notification(
        user_id=assigned_to_id,
        title="مهمة جديدة",
        message=f"تم تعيين لك مهمة: {task_title}",
        notification_type="task_assigned",
        related_id=task_id,
        is_read=False
    )
    
    db.add(notification)
    db.commit()
    
    return {"success": True, "message": "تم إرسال الإشعار بنجاح"}
