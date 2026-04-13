"""
مسارات Firebase لإدارة توكنات الأجهزة والإشعارات الفورية
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from models import User, Notification
from firebase_service import (
    firebase_service,
    send_like_notification,
    send_comment_notification,
    send_friend_request_notification,
    send_message_notification,
    send_task_notification,
    send_group_notification
)

router = APIRouter(prefix="/api/firebase", tags=["Firebase"])


# ==================== Schemas ====================

class DeviceTokenRequest(BaseModel):
    """طلب تسجيل توكن الجهاز"""
    device_token: str
    device_name: Optional[str] = None
    platform: Optional[str] = None  # "android", "ios", "web"


class SendNotificationRequest(BaseModel):
    """طلب إرسال إشعار"""
    user_id: str
    title: str
    body: str
    data: Optional[dict] = None


class SendMulticastRequest(BaseModel):
    """طلب إرسال إشعارات متعددة"""
    user_ids: List[str]
    title: str
    body: str
    data: Optional[dict] = None


class SendTopicNotificationRequest(BaseModel):
    """طلب إرسال إشعار لموضوع"""
    topic: str
    title: str
    body: str
    data: Optional[dict] = None


class SubscribeToTopicRequest(BaseModel):
    """طلب الاشتراك في موضوع"""
    topic: str


# ==================== Device Token Management ====================

@router.post("/register-device")
async def register_device_token(
    request: DeviceTokenRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    تسجيل توكن جهاز جديد للمستخدم
    
    يتم تخزين التوكن في قاعدة البيانات لاستخدامه في إرسال الإشعارات الفورية
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
    
    # إضافة التوكن إلى قائمة التوكنات
    if not user.device_tokens:
        user.device_tokens = []
    
    # تجنب التوكنات المكررة
    if request.device_token not in user.device_tokens:
        user.device_tokens.append(request.device_token)
    
    # تحديث التوكن الأساسي
    user.device_token = request.device_token
    
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "تم تسجيل توكن الجهاز بنجاح",
        "device_token": request.device_token,
        "total_devices": len(user.device_tokens)
    }


@router.delete("/unregister-device")
async def unregister_device_token(
    device_token: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إلغاء تسجيل توكن جهاز
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
    
    if user.device_tokens and device_token in user.device_tokens:
        user.device_tokens.remove(device_token)
        
        # إذا كان هذا هو التوكن الأساسي، حدد التوكن الجديد
        if user.device_token == device_token:
            user.device_token = user.device_tokens[0] if user.device_tokens else None
    
    db.commit()
    
    return {
        "success": True,
        "message": "تم إلغاء تسجيل توكن الجهاز بنجاح",
        "remaining_devices": len(user.device_tokens) if user.device_tokens else 0
    }


@router.get("/devices")
async def get_user_devices(
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    الحصول على قائمة أجهزة المستخدم المسجلة
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
    
    return {
        "user_id": current_user_id,
        "primary_device_token": user.device_token,
        "all_device_tokens": user.device_tokens or [],
        "total_devices": len(user.device_tokens) if user.device_tokens else 0
    }


# ==================== Send Notifications ====================

@router.post("/send-notification")
async def send_notification(
    request: SendNotificationRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعار فوري لمستخدم معين
    
    يتم البحث عن توكن الجهاز الخاص بالمستخدم وإرسال الإشعار عبر Firebase
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    # التحقق من وجود المستخدم المستقبل
    recipient = db.query(User).filter(User.id == request.user_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم المستقبل غير موجود"
        )
    
    # التحقق من وجود توكن جهاز
    if not recipient.device_token:
        # حفظ الإشعار في قاعدة البيانات فقط
        notification = Notification(
            user_id=request.user_id,
            title=request.title,
            message=request.body,
            notification_type="system",
            is_read=False
        )
        db.add(notification)
        db.commit()
        
        return {
            "success": True,
            "message": "تم حفظ الإشعار في قاعدة البيانات (لا يوجد جهاز مسجل)",
            "sent_via_firebase": False
        }
    
    # إرسال الإشعار عبر Firebase
    success = firebase_service.send_notification(
        device_token=recipient.device_token,
        title=request.title,
        body=request.body,
        data=request.data or {}
    )
    
    # حفظ الإشعار في قاعدة البيانات
    notification = Notification(
        user_id=request.user_id,
        title=request.title,
        message=request.body,
        notification_type="system",
        is_read=False
    )
    db.add(notification)
    db.commit()
    
    return {
        "success": success,
        "message": "تم إرسال الإشعار بنجاح" if success else "فشل إرسال الإشعار",
        "sent_via_firebase": success
    }


@router.post("/send-multicast")
async def send_multicast_notification(
    request: SendMulticastRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعارات فورية لعدة مستخدمين
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    # جمع جميع توكنات الأجهزة
    device_tokens = []
    for user_id in request.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.device_token:
            device_tokens.append(user.device_token)
        
        # حفظ الإشعار في قاعدة البيانات
        notification = Notification(
            user_id=user_id,
            title=request.title,
            message=request.body,
            notification_type="system",
            is_read=False
        )
        db.add(notification)
    
    db.commit()
    
    if not device_tokens:
        return {
            "success": True,
            "message": "تم حفظ الإشعارات في قاعدة البيانات (لا توجد أجهزة مسجلة)",
            "sent_via_firebase": False,
            "success_count": 0,
            "failed_count": len(request.user_ids)
        }
    
    # إرسال الإشعارات عبر Firebase
    result = firebase_service.send_multicast(
        device_tokens=device_tokens,
        title=request.title,
        body=request.body,
        data=request.data or {}
    )
    
    return {
        "success": True,
        "message": f"تم إرسال {result['success']} إشعار بنجاح",
        "sent_via_firebase": True,
        "success_count": result['success'],
        "failed_count": result['failed']
    }


@router.post("/send-topic-notification")
async def send_topic_notification(
    request: SendTopicNotificationRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إرسال إشعار فوري لموضوع معين
    
    جميع المستخدمين المشتركين في الموضوع سيتلقون الإشعار
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    # إرسال الإشعار عبر Firebase
    success = firebase_service.send_topic_notification(
        topic=request.topic,
        title=request.title,
        body=request.body,
        data=request.data or {}
    )
    
    return {
        "success": success,
        "message": f"تم إرسال الإشعار للموضوع '{request.topic}' بنجاح" if success else "فشل إرسال الإشعار",
        "topic": request.topic
    }


# ==================== Topic Management ====================

@router.post("/subscribe-topic")
async def subscribe_to_topic(
    request: SubscribeToTopicRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    الاشتراك في موضوع معين
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user or not user.device_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يوجد جهاز مسجل للمستخدم"
        )
    
    # الاشتراك في الموضوع
    success = firebase_service.subscribe_to_topic(
        device_tokens=user.device_tokens,
        topic=request.topic
    )
    
    return {
        "success": success,
        "message": f"تم الاشتراك في الموضوع '{request.topic}' بنجاح" if success else "فشل الاشتراك في الموضوع",
        "topic": request.topic
    }


@router.post("/unsubscribe-topic")
async def unsubscribe_from_topic(
    request: SubscribeToTopicRequest,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إلغاء الاشتراك من موضوع معين
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user or not user.device_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يوجد جهاز مسجل للمستخدم"
        )
    
    # إلغاء الاشتراك من الموضوع
    success = firebase_service.unsubscribe_from_topic(
        device_tokens=user.device_tokens,
        topic=request.topic
    )
    
    return {
        "success": success,
        "message": f"تم إلغاء الاشتراك من الموضوع '{request.topic}' بنجاح" if success else "فشل إلغاء الاشتراك",
        "topic": request.topic
    }


# ==================== Notification Status ====================

@router.get("/firebase-status")
async def get_firebase_status():
    """
    الحصول على حالة خدمة Firebase
    """
    return {
        "firebase_initialized": firebase_service.initialized,
        "status": "✅ Firebase جاهزة" if firebase_service.initialized else "⚠️ Firebase غير مهيأة",
        "message": "يمكنك إرسال الإشعارات الفورية" if firebase_service.initialized else "تحقق من إعدادات Firebase في ملف .env"
    }
