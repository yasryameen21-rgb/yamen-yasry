"""
خدمة Firebase للإشعارات الفورية
"""

import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Optional
import json
from config import settings


class FirebaseService:
    """خدمة Firebase للإشعارات الفورية"""
    
    def __init__(self):
        """تهيئة Firebase"""
        self.initialized = False
        self.init_firebase()
    
    def init_firebase(self):
        """تهيئة Firebase Admin SDK"""
        try:
            # التحقق من وجود بيانات اعتماد Firebase
            if not settings.firebase_project_id:
                print("⚠️ بيانات Firebase غير مكتملة - الإشعارات المحلية فقط")
                return
            
            # معالجة المفتاح الخاص للتعامل مع الرموز المائلة العكسية (\n)
            # تم إضافة معالجة إضافية لإزالة علامات الاقتباس الزائدة إذا وجدت
            private_key = settings.firebase_private_key
            
            if private_key:
                # إزالة علامات الاقتباس في البداية والنهاية إذا كانت موجودة (شائع عند النسخ من .env)
                private_key = private_key.strip("'\"")
                
                # استبدال \\n بـ \n الحقيقية
                if "\\n" in private_key:
                    private_key = private_key.replace("\\n", "\n")
                
                # التأكد من وجود ترويسة وتذييل المفتاح بشكل صحيح
                if "-----BEGIN PRIVATE KEY-----" not in private_key:
                    print("⚠️ تحذير: مفتاح Firebase الخاص قد يكون بتنسيق غير صحيح (مفقود الترويسة)")
            
            # إنشاء بيانات الاعتماد
            cred_dict = {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "private_key_id": settings.firebase_private_key_id,
                "private_key": private_key,
                "client_email": settings.firebase_client_email,
                "client_id": settings.firebase_client_id,
                "auth_uri": settings.firebase_auth_uri,
                "token_uri": settings.firebase_token_uri,
            }
            
            # تهيئة Firebase - التحقق مما إذا كان التطبيق مهيأ بالفعل لتجنب خطأ DuplicateApp
            try:
                firebase_admin.get_app()
                print("ℹ️ تطبيق Firebase مهيأ بالفعل")
            except ValueError:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("✅ تم تهيئة Firebase بنجاح")
            
            self.initialized = True
        
        except Exception as e:
            print(f"❌ خطأ في تهيئة Firebase: {str(e)}")
            self.initialized = False
    
    def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """إرسال إشعار إلى جهاز معين"""
        if not self.initialized or not device_token:
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=device_token
            )
            
            response = messaging.send(message)
            print(f"✅ تم إرسال الإشعار بنجاح: {response}")
            return True
        
        except Exception as e:
            print(f"❌ خطأ في إرسال الإشعار: {str(e)}")
            return False

    # باقي الوظائف (send_multicast, etc.) تظل كما هي في المنطق الأصلي
    def send_multicast(self, device_tokens: List[str], title: str, body: str, data: Optional[dict] = None) -> dict:
        if not self.initialized or not device_tokens: return {"success": 0, "failed": len(device_tokens)}
        try:
            message = messaging.MulticastMessage(notification=messaging.Notification(title=title, body=body), data=data or {}, tokens=device_tokens)
            response = messaging.send_multicast(message)
            return {"success": response.success_count, "failed": response.failure_count}
        except Exception as e:
            print(f"❌ خطأ في إرسال الإشعارات المتعددة: {str(e)}")
            return {"success": 0, "failed": len(device_tokens)}

    def send_topic_notification(self, topic: str, title: str, body: str, data: Optional[dict] = None) -> bool:
        if not self.initialized or not topic: return False
        try:
            message = messaging.Message(notification=messaging.Notification(title=title, body=body), data=data or {}, topic=topic)
            messaging.send(message)
            return True
        except Exception as e:
            print(f"❌ خطأ في إرسال الإشعار للموضوع: {str(e)}")
            return False

    def subscribe_to_topic(self, device_tokens: List[str], topic: str) -> bool:
        if not self.initialized or not device_tokens or not topic: return False
        try:
            messaging.subscribe_to_topic(device_tokens, topic)
            return True
        except Exception as e:
            print(f"❌ خطأ في الاشتراك في الموضوع: {str(e)}")
            return False

    def unsubscribe_from_topic(self, device_tokens: List[str], topic: str) -> bool:
        if not self.initialized or not device_tokens or not topic: return False
        try:
            messaging.unsubscribe_from_topic(device_tokens, topic)
            return True
        except Exception as e:
            print(f"❌ خطأ في إلغاء الاشتراك من الموضوع: {str(e)}")
            return False


# إنشاء مثيل واحد من الخدمة
firebase_service = FirebaseService()

# وظائف مساعدة
def send_like_notification(device_token: str, user_name: str, post_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title="إعجاب جديد 👍", body=f"أعجب {user_name} بمنشورك", data={"type": "like", "post_id": post_id})

def send_comment_notification(device_token: str, user_name: str, comment_text: str, post_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title="تعليق جديد 💬", body=f"{user_name}: {comment_text[:50]}...", data={"type": "comment", "post_id": post_id})

def send_friend_request_notification(device_token: str, user_name: str, user_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title="طلب صداقة جديد 👋", body=f"أرسل لك {user_name} طلب صداقة", data={"type": "friend_request", "user_id": user_id})

def send_message_notification(device_token: str, user_name: str, message_text: str, conversation_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title=f"رسالة من {user_name} 📨", body=message_text[:50], data={"type": "message", "conversation_id": conversation_id})

def send_task_notification(device_token: str, task_title: str, assigned_by: str, task_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title="مهمة جديدة ✅", body=f"عين لك {assigned_by}: {task_title}", data={"type": "task", "task_id": task_id})

def send_group_notification(device_token: str, group_name: str, message: str, group_id: str) -> bool:
    return firebase_service.send_notification(device_token=device_token, title=f"رسالة في {group_name} 👥", body=message[:50], data={"type": "group", "group_id": group_id})
