"""
نماذج قاعدة البيانات باستخدام SQLAlchemy
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Table, Enum, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class UserRole(str, enum.Enum):
    """أدوار المستخدمين"""
    USER = "user"
    ADMIN = "admin"
    OWNER = "owner"


class PostType(str, enum.Enum):
    """أنواع المنشورات"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class ReactionType(str, enum.Enum):
    """أنواع التفاعلات"""
    LIKE = "like"
    LOVE = "love"
    HAHA = "haha"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class NotificationType(str, enum.Enum):
    """أنواع الإشعارات"""
    LIKE = "like"
    COMMENT = "comment"
    TASK_ASSIGNED = "task_assigned"
    GROUP_INVITE = "group_invite"
    ADMIN_ALERT = "admin_alert"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    """أنواع الرسائل"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    EMOJI = "emoji"
    LINK = "link"
    LIVE_STARTED = "live_started"
    LIVE_ENDED = "live_ended"
    COMMENT = "comment"

class LiveStreamStatus(str, enum.Enum):
    """حالات البث المباشر"""
    STARTING = "starting"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"


class RecordingStatus(str, enum.Enum):
    """حالات التسجيل"""
    PENDING = "pending"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GroupPrivacy(str, enum.Enum):
    """خصوصية المجموعات"""
    PUBLIC = "public"    # عامة: يمكن للجميع البحث عنها والانضمام
    CLOSED = "closed"    # مغلقة: تظهر في البحث ولكن الانضمام بطلب
    SECRET = "secret"    # سرية: لا تظهر في البحث والانضمام بدعوة فقط

class GroupType(str, enum.Enum):
    """أنواع المجموعات"""
    FAMILY = "family"
    WORK = "work"
    CUSTOM = "custom"
    MARKET = "market"

class MarketplaceCategory(str, enum.Enum):
    """تصنيفات السوق"""
    ELECTRONICS = "electronics"
    VEHICLES = "vehicles"
    REAL_ESTATE = "real_estate"
    FASHION = "fashion"
    HOME = "home"
    OTHER = "other"

class MarketplaceItemStatus(str, enum.Enum):
    """حالة المنتج في السوق"""
    AVAILABLE = "available"
    SOLD = "sold"
    PENDING = "pending"


class AppTaskStatus(str, enum.Enum):
    """حالات المهام"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# جداول الربط (Many-to-Many)
user_friends = Table(
    'user_friends',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('friend_id', String, ForeignKey('users.id'))
)

group_members = Table(
    'group_members',
    Base.metadata,
    Column('group_id', String, ForeignKey('groups.id')),
    Column('user_id', String, ForeignKey('users.id'))
)

conversation_participants = Table(
    'conversation_participants',
    Base.metadata,
    Column('conversation_id', String, ForeignKey('conversations.id')),
    Column('user_id', String, ForeignKey('users.id'))
)


class User(Base):
    """نموذج المستخدم"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # صور وملف شخصي
    profile_image_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # حالة المستخدم
    is_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    is_muted_from_commenting = Column(Boolean, default=False)
    is_muted_from_posting = Column(Boolean, default=False)
    
    # الإعدادات
    dark_mode_enabled = Column(Boolean, default=False)
    primary_color = Column(String, default="#2196F3")
    
    # Firebase Device Token للإشعارات الفورية
    device_token = Column(String, nullable=True, index=True)
    device_tokens = Column(JSON, default=[])  # قائمة بجميع توكنات الأجهزة المسجلة
    
    # الأوقات
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # التشفير (End-to-End Encryption)
    public_key = Column(Text, nullable=True) # المفتاح العام للمستخدم لتمكين الآخرين من التشفير له
    encrypted_private_key = Column(Text, nullable=True) # المفتاح الخاص مشفراً بكلمة مرور المستخدم (اختياري للتخزين السحابي)
    
    # الأصدقاء
    friends = relationship(
        "User",
        secondary=user_friends,
        primaryjoin=id == user_friends.c.user_id,
        secondaryjoin=id == user_friends.c.friend_id,
        backref="friend_of"
    )
    
    # العلاقات
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    messages = relationship("Message", back_populates="sender")
    notifications = relationship("Notification", back_populates="user")
    tasks = relationship(
        "SharedTask",
        back_populates="assigned_user",
        foreign_keys="SharedTask.assigned_to"
    )
    created_tasks = relationship(
        "SharedTask",
        foreign_keys="SharedTask.created_by",
        back_populates="creator"
    )
    groups = relationship("Group", secondary=group_members, back_populates="members")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    stories = relationship("Story", back_populates="author")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


class Group(Base):
    """نموذج المجموعة"""
    __tablename__ = "groups"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    group_type = Column(Enum(GroupType), default=GroupType.CUSTOM)
    privacy = Column(Enum(GroupPrivacy), default=GroupPrivacy.PUBLIC)
    admin_id = Column(String, ForeignKey('users.id'), nullable=False)
    group_image_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    members = relationship("User", secondary=group_members, back_populates="groups")
    posts = relationship("Post", back_populates="group")
    tasks = relationship("SharedTask", back_populates="group")
    marketplace_items = relationship("MarketplaceItem", back_populates="group")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name})>"

class MarketplaceItem(Base):
    """نموذج منتج في السوق"""
    __tablename__ = "marketplace_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String, ForeignKey('users.id'), nullable=False)
    group_id = Column(String, ForeignKey('groups.id'), nullable=True) # إذا كان المنتج داخل مجموعة معينة
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    currency = Column(String, default="YER")
    category = Column(Enum(MarketplaceCategory), default=MarketplaceCategory.OTHER)
    status = Column(Enum(MarketplaceItemStatus), default=MarketplaceItemStatus.AVAILABLE)
    
    location = Column(String, nullable=True)
    image_urls = Column(JSON, default=[]) # قائمة بروابط الصور
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    seller = relationship("User", backref="marketplace_items")
    group = relationship("Group", back_populates="marketplace_items")
    
    def __repr__(self):
        return f"<MarketplaceItem(id={self.id}, title={self.title})>"


class Post(Base):
    """نموذج المنشور"""
    __tablename__ = "posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    group_id = Column(String, ForeignKey('groups.id'), nullable=True)
    
    content = Column(Text, nullable=False)
    post_type = Column(Enum(PostType), default=PostType.TEXT)
    media_url = Column(String, nullable=True)
    
    # معاينة الروابط
    link_preview_url = Column(String, nullable=True)
    link_preview_title = Column(String, nullable=True)
    link_preview_description = Column(Text, nullable=True)
    link_preview_image = Column(String, nullable=True)
    
    # الحالة
    is_hidden = Column(Boolean, default=False)
    shares_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # التفاعلات (JSON)
    reactions = Column(JSON, default={})
    
    # العلاقات
    author = relationship("User", back_populates="posts")
    group = relationship("Group", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(id={self.id}, user_id={self.user_id})>"


class Comment(Base):
    """نموذج التعليق"""
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey('posts.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    content = Column(Text, nullable=False)
    
    # التفاعلات (JSON)
    reactions = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"


class Notification(Base):
    """نموذج الإشعار"""
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    related_id = Column(String, nullable=True)
    
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id})>"


class Message(Base):
    """نموذج الرسالة"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    sender_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    media_url = Column(String, nullable=True)
    
    reply_to_message_id = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    
    # التشفير
    is_encrypted = Column(Boolean, default=False)
    encryption_v = Column(String, default="1.0") # إصدار خوارزمية التشفير
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)
    
    # التفاعلات (JSON)
    reactions = Column(JSON, default={})
    
    # العلاقات
    sender = relationship("User", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id})>"


class Conversation(Base):
    """نموذج المحادثة"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    is_group_chat = Column(Boolean, default=False)
    group_image_url = Column(String, nullable=True)
    
    is_muted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    unread_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_time = Column(DateTime, nullable=True)
    
    # العلاقات
    participants = relationship("User", secondary=conversation_participants)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, name={self.name})>"


class SharedTask(Base):
    """نموذج المهمة المشتركة"""
    __tablename__ = "shared_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey('groups.id'), nullable=False)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    assigned_to = Column(String, ForeignKey('users.id'), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(Enum(AppTaskStatus), default=AppTaskStatus.PENDING)
    priority = Column(Integer, default=1)
    
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    group = relationship("Group", back_populates="tasks")
    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="tasks"
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tasks"
    )
    
    def __repr__(self):
        return f"<SharedTask(id={self.id}, title={self.title})>"


class Story(Base):
    """نموذج القصة"""
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    media_url = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # image أو video
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # المشاهدات (JSON)
    viewed_by_users = Column(JSON, default=[])
    
    # العلاقات
    author = relationship("User", back_populates="stories")
    
    def __repr__(self):
        return f"<Story(id={self.id}, user_id={self.user_id})>"


class CloudRecording(Base):
    """نموذج تسجيل البث السحابي (VOD)"""
    __tablename__ = "cloud_recordings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    live_stream_id = Column(String, ForeignKey('live_streams.id'), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # معلومات الملف
    video_url = Column(String, nullable=False)  # رابط الفيديو المسجل
    thumbnail_url = Column(String, nullable=True)  # صورة مصغرة
    duration_seconds = Column(Integer, default=0)  # مدة الفيديو
    file_size_mb = Column(Integer, default=0)  # حجم الملف
    video_quality = Column(String, default="720p")  # جودة الفيديو
    
    # معلومات التسجيل
    recording_status = Column(Enum(RecordingStatus), default=RecordingStatus.COMPLETED)
    view_count = Column(Integer, default=0)  # عدد المشاهدات
    
    # الخصوصية
    is_public = Column(Boolean, default=True)  # هل البث المسجل عام أم خاص
    allowed_viewers = Column(JSON, default=[])  # قائمة المستخدمين المسموح لهم بالمشاهدة (إذا كان خاص)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # تاريخ انتهاء صلاحية التسجيل
    
    # العلاقات
    live_stream = relationship("LiveStream", back_populates="recordings")
    
    def __repr__(self):
        return f"<CloudRecording(id={self.id}, live_stream_id={self.live_stream_id})>"


class UserSettings(Base):
    """نموذج إعدادات المستخدم"""
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True, nullable=False)
    
    dark_mode_enabled = Column(Boolean, default=False)
    primary_color = Column(String, default="#2196F3")
    
    notifications_enabled = Column(Boolean, default=True)
    email_notifications_enabled = Column(Boolean, default=True)
    
    show_profile_to_everyone = Column(Boolean, default=True)
    allow_messages_from_strangers = Column(Boolean, default=False)
    allow_friend_requests = Column(Boolean, default=True)
    
    privacy_level = Column(String, default="friends")  # everyone, friends, private
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id})>"


class LiveStream(Base):
    """نموذج البث المباشر"""
    __tablename__ = "live_streams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id = Column(String, ForeignKey('users.id'), nullable=False)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=True) # إذا كان البث داخل محادثة
    
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(LiveStreamStatus), default=LiveStreamStatus.STARTING)
    
    # معلومات WebRTC (Signaling)
    sdp_offer = Column(Text, nullable=True)
    sdp_answer = Column(Text, nullable=True)
    
    viewer_count = Column(Integer, default=0)
    peak_viewer_count = Column(Integer, default=0)  # أقصى عدد مشاهدين
    
    # معلومات التسجيل
    is_recording_enabled = Column(Boolean, default=True)
    recording_status = Column(Enum(RecordingStatus), nullable=True)
    recording_url = Column(String, nullable=True)  # رابط الفيديو المسجل
    recording_duration = Column(Integer, default=0)  # مدة التسجيل بالثواني
    recording_size_mb = Column(Integer, default=0)  # حجم الملف بـ MB
    thumbnail_url = Column(String, nullable=True)  # صورة مصغرة للبث
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    recording_completed_at = Column(DateTime, nullable=True)
    
    # العلاقات
    host = relationship("User", backref="hosted_streams")
    conversation = relationship("Conversation", backref="live_streams")
    recordings = relationship("CloudRecording", back_populates="live_stream", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LiveStream(id={self.id}, host_id={self.host_id}, status={self.status})>"


class FollowRelation(Base):
    """علاقة متابعة بين مستخدمين"""
    __tablename__ = "follow_relations"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_relation"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, ForeignKey("users.id"), nullable=False)
    following_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FriendRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class FriendRequest(Base):
    """طلبات الصداقة"""
    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("sender_id", "receiver_id", name="uq_friend_request_pair"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(Enum(FriendRequestStatus), default=FriendRequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)


class SavedPost(Base):
    """المنشورات المحفوظة"""
    __tablename__ = "saved_posts"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_saved_post"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PostShare(Base):
    """سجل إعادة نشر/مشاركة المنشورات"""
    __tablename__ = "post_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    original_post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    repost_post_id = Column(String, ForeignKey("posts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ContentReport(Base):
    """بلاغات المحتوى والمستخدمين"""
    __tablename__ = "content_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LiveRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class LiveJoinRequest(Base):
    """طلبات الانضمام للبث المباشر"""
    __tablename__ = "live_join_requests"
    __table_args__ = (
        UniqueConstraint("stream_id", "requester_id", name="uq_live_join_request_pair"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stream_id = Column(String, ForeignKey("live_streams.id"), nullable=False)
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    status = Column(Enum(LiveRequestStatus), default=LiveRequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    stream = relationship("LiveStream", backref="join_requests")

    def __repr__(self):
        return f"<LiveJoinRequest(id={self.id}, stream_id={self.stream_id}, requester_id={self.requester_id})>"
