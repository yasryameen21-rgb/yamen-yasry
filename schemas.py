"""
نماذج Pydantic للتحقق من البيانات والاستجابة
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ==================== تعريفات Enum ====================

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    OWNER = "owner"


class PostTypeEnum(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class ReactionTypeEnum(str, Enum):
    LIKE = "like"
    LOVE = "love"
    HAHA = "haha"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class NotificationTypeEnum(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    TASK_ASSIGNED = "task_assigned"
    GROUP_INVITE = "group_invite"
    ADMIN_ALERT = "admin_alert"
    SYSTEM = "system"


# ==================== نماذج المصادقة ====================

class UserRegister(BaseModel):
    """نموذج التسجيل"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: Optional[str] = None


class UserLogin(BaseModel):
    """نموذج تسجيل الدخول"""
    email: EmailStr
    password: str


class ChangePassword(BaseModel):
    """نموذج تغيير كلمة المرور"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class ResetPassword(BaseModel):
    """نموذج إعادة تعيين كلمة المرور"""
    email: EmailStr


class VerifyEmail(BaseModel):
    """نموذج التحقق من البريد الإلكتروني"""
    email: EmailStr
    verification_code: str


# ==================== نماذج المستخدم ====================

class UserUpdate(BaseModel):
    """نموذج تحديث المستخدم"""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    dark_mode_enabled: Optional[bool] = None
    primary_color: Optional[str] = None
    public_key: Optional[str] = None
    encrypted_private_key: Optional[str] = None


class UserResponse(BaseModel):
    """نموذج استجابة المستخدم"""
    id: str
    name: str
    email: str
    phone_number: Optional[str]
    role: UserRoleEnum
    profile_image_url: Optional[str]
    cover_image_url: Optional[str]
    bio: Optional[str]
    is_verified: bool
    is_banned: bool
    dark_mode_enabled: bool
    primary_color: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """نموذج استجابة تفاصيل المستخدم"""
    friends_count: int = 0
    posts_count: int = 0
    groups_count: int = 0


# ==================== نماذج المنشورات ====================

class PostCreate(BaseModel):
    """نموذج إنشاء منشور"""
    content: str = Field(..., min_length=1, max_length=5000)
    post_type: PostTypeEnum = PostTypeEnum.TEXT
    media_url: Optional[str] = None
    group_id: Optional[str] = None
    link_preview_url: Optional[str] = None
    link_preview_title: Optional[str] = None
    link_preview_description: Optional[str] = None
    link_preview_image: Optional[str] = None


class PostUpdate(BaseModel):
    """نموذج تحديث منشور"""
    content: Optional[str] = None
    media_url: Optional[str] = None
    link_preview_url: Optional[str] = None
    link_preview_title: Optional[str] = None
    link_preview_description: Optional[str] = None
    link_preview_image: Optional[str] = None


class PostResponse(BaseModel):
    """نموذج استجابة المنشور"""
    id: str
    user_id: str
    content: str
    post_type: PostTypeEnum
    media_url: Optional[str]
    group_id: Optional[str]
    is_hidden: bool
    shares_count: int
    reactions: Dict = {}
    link_preview_url: Optional[str]
    link_preview_title: Optional[str]
    link_preview_description: Optional[str]
    link_preview_image: Optional[str]
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0
    
    class Config:
        from_attributes = True


# ==================== نماذج التعليقات ====================

class CommentCreate(BaseModel):
    """نموذج إنشاء تعليق"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """نموذج استجابة التعليق"""
    id: str
    post_id: str
    user_id: str
    content: str
    reactions: Dict = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== نماذج الإشعارات ====================

class NotificationCreate(BaseModel):
    """نموذج إنشاء إشعار"""
    title: str
    message: str
    notification_type: NotificationTypeEnum
    related_id: Optional[str] = None


class NotificationResponse(BaseModel):
    """نموذج استجابة الإشعار"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationTypeEnum
    related_id: Optional[str]
    is_read: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== نماذج الرسائل ====================

class MessageCreate(BaseModel):
    """نموذج إنشاء رسالة"""
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = "text"
    media_url: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    is_encrypted: bool = False
    encryption_v: str = "1.0"


class MessageResponse(BaseModel):
    """نموذج استجابة الرسالة"""
    id: str
    conversation_id: str
    sender_id: str
    content: str
    message_type: str
    media_url: Optional[str]
    is_read: bool
    is_encrypted: bool
    encryption_v: str
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime]
    reactions: Dict = {}
    
    class Config:
        from_attributes = True


# ==================== نماذج المحادثات ====================

class ConversationCreate(BaseModel):
    """نموذج إنشاء محادثة"""
    name: Optional[str] = None
    is_group_chat: bool = False
    participant_ids: List[str] = []


class ConversationResponse(BaseModel):
    """نموذج استجابة المحادثة"""
    id: str
    name: Optional[str]
    is_group_chat: bool
    is_muted: bool
    is_pinned: bool
    unread_count: int
    created_at: datetime
    last_message_time: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== نماذج المهام ====================

class TaskCreate(BaseModel):
    """نموذج إنشاء مهمة"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    group_id: str
    assigned_to: str
    due_date: Optional[datetime] = None
    priority: int = 1


class TaskUpdate(BaseModel):
    """نموذج تحديث مهمة"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None


class TaskResponse(BaseModel):
    """نموذج استجابة المهمة"""
    id: str
    group_id: str
    created_by: str
    assigned_to: str
    title: str
    description: Optional[str]
    status: str
    priority: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== نماذج المجموعات ====================

class GroupCreate(BaseModel):
    """نموذج إنشاء مجموعة"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    group_type: str = "custom"
    group_image_url: Optional[str] = None


class GroupUpdate(BaseModel):
    """نموذج تحديث مجموعة"""
    name: Optional[str] = None
    description: Optional[str] = None
    group_image_url: Optional[str] = None


class GroupResponse(BaseModel):
    """نموذج استجابة المجموعة"""
    id: str
    name: str
    description: Optional[str]
    group_type: str
    admin_id: str
    group_image_url: Optional[str]
    members_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== نماذج القصص ====================

class StoryCreate(BaseModel):
    """نموذج إنشاء قصة"""
    media_url: str
    media_type: str = "image"


class StoryResponse(BaseModel):
    """نموذج استجابة القصة"""
    id: str
    user_id: str
    media_url: str
    media_type: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    view_count: int = 0
    
    class Config:
        from_attributes = True


# ==================== نماذج الإعدادات ====================

class UserSettingsUpdate(BaseModel):
    """نموذج تحديث إعدادات المستخدم"""
    dark_mode_enabled: Optional[bool] = None
    primary_color: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    show_profile_to_everyone: Optional[bool] = None
    allow_messages_from_strangers: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    privacy_level: Optional[str] = None


class UserSettingsResponse(BaseModel):
    """نموذج استجابة إعدادات المستخدم"""
    user_id: str
    dark_mode_enabled: bool
    primary_color: str
    notifications_enabled: bool
    email_notifications_enabled: bool
    show_profile_to_everyone: bool
    allow_messages_from_strangers: bool
    allow_friend_requests: bool
    privacy_level: str
    last_updated: datetime
    
    class Config:
        from_attributes = True


# ==================== نماذج الاستجابة العامة ====================

class SuccessResponse(BaseModel):
    """نموذج استجابة النجاح"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """نموذج استجابة الخطأ"""
    success: bool = False
    message: str
    error_code: Optional[str] = None

# ==================== نماذج التوكن ====================

class Token(BaseModel):
    """نموذج التوكن"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class OnboardingRegistrationRequest(BaseModel):
    """نموذج التسجيل السريع من شاشة الإنشاء الجديدة"""
    first_name: str = Field(..., min_length=2, max_length=60)
    last_name: str = Field(..., min_length=2, max_length=60)
    date_of_birth: Optional[datetime] = None
    contact_method: str = Field(..., pattern="^(phone|email)$")
    contact: str = Field(..., min_length=3, max_length=120)


class OnboardingProfileResponse(BaseModel):
    """ملف تعريف مبسط يرجع بعد التسجيل السريع"""
    id: str
    user_id: str
    first_name: str
    last_name: str
    display_name: str
    date_of_birth: Optional[datetime] = None
    contact_method: str
    contact: str
    created_at: datetime


class OnboardingAuthResponse(BaseModel):
    """استجابة التسجيل السريع مع التوكنات"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    display_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    profile: OnboardingProfileResponse


class TokenData(BaseModel):
    """نموذج بيانات التوكن"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ==================== نماذج البث المباشر ====================

class LiveStreamStatusEnum(str, Enum):
    STARTING = "starting"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class RecordingStatusEnum(str, Enum):
    PENDING = "pending"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LiveStreamCreate(BaseModel):
    """نموذج بدء بث مباشر"""
    conversation_id: Optional[str] = None
    title: Optional[str] = None
    sdp_offer: Optional[str] = None


class LiveStreamUpdate(BaseModel):
    """نموذج تحديث بث مباشر"""
    status: Optional[LiveStreamStatusEnum] = None
    sdp_answer: Optional[str] = None
    viewer_count: Optional[int] = None


class LiveStreamResponse(BaseModel):
    """نموذج استجابة البث المباشر"""
    id: str
    host_id: str
    conversation_id: Optional[str]
    title: Optional[str]
    description: Optional[str]
    status: LiveStreamStatusEnum
    sdp_offer: Optional[str]
    sdp_answer: Optional[str]
    viewer_count: int
    peak_viewer_count: int
    is_recording_enabled: bool
    recording_status: Optional[RecordingStatusEnum]
    recording_url: Optional[str]
    recording_duration: int
    recording_size_mb: int
    thumbnail_url: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    recording_completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CloudRecordingCreate(BaseModel):
    """نموذج إنشاء تسجيل سحابي"""
    live_stream_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: int = 0
    file_size_mb: int = 0
    video_quality: str = "720p"
    is_public: bool = True
    allowed_viewers: List[str] = []
    expires_at: Optional[datetime] = None


class CloudRecordingUpdate(BaseModel):
    """نموذج تحديث تسجيل سحابي"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    allowed_viewers: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class CloudRecordingResponse(BaseModel):
    """نموذج استجابة التسجيل السحابي"""
    id: str
    live_stream_id: str
    title: str
    description: Optional[str]
    video_url: str
    thumbnail_url: Optional[str]
    duration_seconds: int
    file_size_mb: int
    video_quality: str
    recording_status: RecordingStatusEnum
    view_count: int
    is_public: bool
    allowed_viewers: List[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SignalingMessage(BaseModel):
    """نموذج رسالة Signaling لـ WebRTC"""
    type: str # 'offer', 'answer', 'candidate'
    payload: Dict
    target_user_id: Optional[str] = None

# ==================== نماذج OTP والمصادقة المتقدمة ====================

class OtpRequest(BaseModel):
    """نموذج طلب إرسال رمز التحقق"""
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class OtpVerify(BaseModel):
    """نموذج التحقق من رمز التحقق"""
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    otp_code: str
