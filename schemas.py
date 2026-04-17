"""
نماذج Pydantic للتحقق من البيانات والاستجابة
"""

from pydantic import BaseModel, EmailStr, Field, AliasChoices, ConfigDict
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


class MarketplaceItemCreate(BaseModel):
    """نموذج إنشاء عنصر في السوق"""
    group_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    price: int = Field(..., ge=0)
    currency: str = "YER"
    category: str = "other"
    location: Optional[str] = None
    image_urls: List[str] = []


class MarketplaceItemUpdate(BaseModel):
    """نموذج تحديث عنصر في السوق"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    image_urls: Optional[List[str]] = None


class MarketplaceItemResponse(BaseModel):
    """نموذج استجابة عنصر في السوق"""
    id: str
    seller_id: str
    group_id: Optional[str]
    title: str
    description: str
    price: int
    currency: str
    category: str
    status: str
    location: Optional[str]
    image_urls: List[str] = []
    created_at: datetime
    updated_at: datetime

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


class FollowResponse(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendRequestCreate(BaseModel):
    message: Optional[str] = Field(default=None, max_length=500)


class FriendRequestResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    message: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


class RepostCreate(BaseModel):
    content: Optional[str] = Field(default=None, max_length=1000)


class SavedPostResponse(BaseModel):
    id: str
    user_id: str
    post_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostStatsResponse(BaseModel):
    post_id: str
    likes_count: int
    comments_count: int
    shares_count: int
    saves_count: int
    reactions_breakdown: Dict[str, int] = {}


class ReportCreate(BaseModel):
    target_type: str = Field(..., pattern="^(post|comment|user|live)$")
    target_id: str = Field(..., min_length=1, max_length=128)
    reason: str = Field(..., min_length=2, max_length=100)
    details: Optional[str] = Field(default=None, max_length=1000)


class ReportResponse(BaseModel):
    id: str
    reporter_id: str
    target_type: str
    target_id: str
    reason: str
    details: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|reviewing|resolved|rejected)$")


class LiveJoinRequestCreate(BaseModel):
    note: Optional[str] = Field(default=None, max_length=500)


class LiveJoinRequestResponse(BaseModel):
    id: str
    stream_id: str
    requester_id: str
    note: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


class LiveStreamStatsResponse(BaseModel):
    stream_id: str
    viewer_count: int
    peak_viewer_count: int
    pending_join_requests: int
    approved_join_requests: int
    rejected_join_requests: int


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
    password: str = Field(..., min_length=8, max_length=128)
    verification_code: str = Field(..., min_length=4, max_length=8)


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
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("conversation_id", "conversationId"), serialization_alias="conversationId")
    title: Optional[str] = None
    sdp_offer: Optional[str] = Field(default=None, validation_alias=AliasChoices("sdp_offer", "sdpOffer"), serialization_alias="sdpOffer")


class LiveStreamUpdate(BaseModel):
    """نموذج تحديث بث مباشر"""
    model_config = ConfigDict(populate_by_name=True)

    status: Optional[LiveStreamStatusEnum] = None
    sdp_answer: Optional[str] = Field(default=None, validation_alias=AliasChoices("sdp_answer", "sdpAnswer"), serialization_alias="sdpAnswer")
    viewer_count: Optional[int] = Field(default=None, validation_alias=AliasChoices("viewer_count", "viewerCount"), serialization_alias="viewerCount")


class LiveStreamResponse(BaseModel):
    """نموذج استجابة البث المباشر"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    host_id: str = Field(validation_alias=AliasChoices("host_id", "hostId"), serialization_alias="hostId")
    conversation_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("conversation_id", "conversationId"), serialization_alias="conversationId")
    title: Optional[str]
    description: Optional[str]
    status: LiveStreamStatusEnum
    sdp_offer: Optional[str] = Field(default=None, validation_alias=AliasChoices("sdp_offer", "sdpOffer"), serialization_alias="sdpOffer")
    sdp_answer: Optional[str] = Field(default=None, validation_alias=AliasChoices("sdp_answer", "sdpAnswer"), serialization_alias="sdpAnswer")
    viewer_count: int = Field(validation_alias=AliasChoices("viewer_count", "viewerCount"), serialization_alias="viewerCount")
    peak_viewer_count: int = Field(validation_alias=AliasChoices("peak_viewer_count", "peakViewerCount"), serialization_alias="peakViewerCount")
    is_recording_enabled: bool = Field(validation_alias=AliasChoices("is_recording_enabled", "isRecordingEnabled"), serialization_alias="isRecordingEnabled")
    recording_status: Optional[RecordingStatusEnum] = Field(default=None, validation_alias=AliasChoices("recording_status", "recordingStatus"), serialization_alias="recordingStatus")
    recording_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("recording_url", "recordingUrl"), serialization_alias="recordingUrl")
    recording_duration: int = Field(validation_alias=AliasChoices("recording_duration", "recordingDuration"), serialization_alias="recordingDuration")
    recording_size_mb: int = Field(validation_alias=AliasChoices("recording_size_mb", "recordingSizeMb"), serialization_alias="recordingSizeMb")
    thumbnail_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("thumbnail_url", "thumbnailUrl"), serialization_alias="thumbnailUrl")
    started_at: datetime = Field(validation_alias=AliasChoices("started_at", "startedAt"), serialization_alias="startedAt")
    ended_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("ended_at", "endedAt"), serialization_alias="endedAt")
    recording_completed_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("recording_completed_at", "recordingCompletedAt"), serialization_alias="recordingCompletedAt")


class CloudRecordingCreate(BaseModel):
    """نموذج إنشاء تسجيل سحابي"""
    model_config = ConfigDict(populate_by_name=True)

    live_stream_id: str = Field(validation_alias=AliasChoices("live_stream_id", "liveStreamId"), serialization_alias="liveStreamId")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: str = Field(validation_alias=AliasChoices("video_url", "videoUrl"), serialization_alias="videoUrl")
    thumbnail_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("thumbnail_url", "thumbnailUrl"), serialization_alias="thumbnailUrl")
    duration_seconds: int = Field(default=0, validation_alias=AliasChoices("duration_seconds", "durationSeconds"), serialization_alias="durationSeconds")
    file_size_mb: int = Field(default=0, validation_alias=AliasChoices("file_size_mb", "fileSizeMb"), serialization_alias="fileSizeMb")
    video_quality: str = Field(default="720p", validation_alias=AliasChoices("video_quality", "videoQuality"), serialization_alias="videoQuality")
    is_public: bool = Field(default=True, validation_alias=AliasChoices("is_public", "isPublic"), serialization_alias="isPublic")
    allowed_viewers: List[str] = Field(default_factory=list, validation_alias=AliasChoices("allowed_viewers", "allowedViewers"), serialization_alias="allowedViewers")
    expires_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("expires_at", "expiresAt"), serialization_alias="expiresAt")


class CloudRecordingUpdate(BaseModel):
    """نموذج تحديث تسجيل سحابي"""
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = Field(default=None, validation_alias=AliasChoices("is_public", "isPublic"), serialization_alias="isPublic")
    allowed_viewers: Optional[List[str]] = Field(default=None, validation_alias=AliasChoices("allowed_viewers", "allowedViewers"), serialization_alias="allowedViewers")
    expires_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("expires_at", "expiresAt"), serialization_alias="expiresAt")
    recording_status: Optional[RecordingStatusEnum] = Field(default=None, validation_alias=AliasChoices("recording_status", "recordingStatus"), serialization_alias="recordingStatus")


class CloudRecordingResponse(BaseModel):
    """نموذج استجابة التسجيل السحابي"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    live_stream_id: str = Field(validation_alias=AliasChoices("live_stream_id", "liveStreamId"), serialization_alias="liveStreamId")
    title: str
    description: Optional[str]
    video_url: str = Field(validation_alias=AliasChoices("video_url", "videoUrl"), serialization_alias="videoUrl")
    thumbnail_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("thumbnail_url", "thumbnailUrl"), serialization_alias="thumbnailUrl")
    duration_seconds: int = Field(validation_alias=AliasChoices("duration_seconds", "durationSeconds"), serialization_alias="durationSeconds")
    file_size_mb: int = Field(validation_alias=AliasChoices("file_size_mb", "fileSizeMb"), serialization_alias="fileSizeMb")
    video_quality: str = Field(validation_alias=AliasChoices("video_quality", "videoQuality"), serialization_alias="videoQuality")
    recording_status: RecordingStatusEnum = Field(validation_alias=AliasChoices("recording_status", "recordingStatus"), serialization_alias="recordingStatus")
    view_count: int = Field(validation_alias=AliasChoices("view_count", "viewCount"), serialization_alias="viewCount")
    is_public: bool = Field(validation_alias=AliasChoices("is_public", "isPublic"), serialization_alias="isPublic")
    allowed_viewers: List[str] = Field(default_factory=list, validation_alias=AliasChoices("allowed_viewers", "allowedViewers"), serialization_alias="allowedViewers")
    created_at: datetime = Field(validation_alias=AliasChoices("created_at", "createdAt"), serialization_alias="createdAt")
    updated_at: datetime = Field(validation_alias=AliasChoices("updated_at", "updatedAt"), serialization_alias="updatedAt")
    expires_at: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("expires_at", "expiresAt"), serialization_alias="expiresAt")


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
