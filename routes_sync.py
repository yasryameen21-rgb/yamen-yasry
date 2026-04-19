"""
مسارات المزامنة الجماعية (Batch Sync)
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple, Type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_user
from models import (
    CloudRecording,
    Comment,
    Conversation,
    Group,
    LiveStream,
    GroupType,
    MarketplaceCategory,
    MarketplaceItem,
    MarketplaceItemStatus,
    Message,
    MessageType,
    Notification,
    NotificationType,
    Post,
    PostType,
    RecordingStatus,
    SharedTask,
    Story,
    User,
    UserRole,
    AppTaskStatus,
)
import schemas

router = APIRouter(
    prefix="/api/sync",
    tags=["Sync"],
)


ENTITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "users": {
        "model": User,
        "fields": {
            "name", "email", "phone_number", "bio", "profile_image_url", "cover_image_url",
            "is_verified", "is_banned", "dark_mode_enabled", "primary_color",
            "public_key", "encrypted_private_key", "device_token", "device_tokens", "last_login"
        },
        "owner_field": None,
        "enum_fields": {"role": UserRole},
    },
    "posts": {
        "model": Post,
        "fields": {
            "user_id", "group_id", "content", "post_type", "media_url", "is_hidden", "shares_count",
            "reactions", "link_preview_url", "link_preview_title", "link_preview_description", "link_preview_image",
            "created_at", "updated_at"
        },
        "owner_field": "user_id",
        "enum_fields": {"post_type": PostType},
    },
    "comments": {
        "model": Comment,
        "fields": {"post_id", "user_id", "content", "reactions", "created_at", "updated_at"},
        "owner_field": "user_id",
        "enum_fields": {},
    },
    "messages": {
        "model": Message,
        "fields": {
            "conversation_id", "sender_id", "content", "message_type", "media_url", "reply_to_message_id",
            "is_read", "is_encrypted", "encryption_v", "reactions", "created_at", "updated_at", "edited_at"
        },
        "owner_field": "sender_id",
        "enum_fields": {"message_type": MessageType},
    },
    "tasks": {
        "model": SharedTask,
        "fields": {
            "group_id", "created_by", "assigned_to", "title", "description", "status", "priority",
            "due_date", "created_at", "updated_at"
        },
        "owner_field": "created_by",
        "enum_fields": {"status": AppTaskStatus},
    },
    "stories": {
        "model": Story,
        "fields": {"user_id", "media_url", "media_type", "created_at", "updated_at", "expires_at", "viewed_by_users"},
        "owner_field": "user_id",
        "enum_fields": {},
    },
    "notifications": {
        "model": Notification,
        "fields": {"user_id", "title", "message", "notification_type", "related_id", "is_read", "created_at", "updated_at"},
        "owner_field": "user_id",
        "enum_fields": {"notification_type": NotificationType},
    },
    "groups": {
        "model": Group,
        "fields": {"name", "description", "group_type", "admin_id", "group_image_url", "cover_image_url", "created_at", "updated_at"},
        "owner_field": "admin_id",
        "enum_fields": {"group_type": GroupType},
    },
    "marketplace_items": {
        "model": MarketplaceItem,
        "fields": {"seller_id", "group_id", "title", "description", "price", "currency", "category", "status", "location", "image_urls", "created_at", "updated_at"},
        "owner_field": "seller_id",
        "enum_fields": {"category": MarketplaceCategory, "status": MarketplaceItemStatus},
    },
    "cloud_recordings": {
        "model": CloudRecording,
        "fields": {"live_stream_id", "title", "description", "video_url", "thumbnail_url", "duration_seconds", "file_size_mb", "video_quality", "recording_status", "view_count", "is_public", "allowed_viewers", "created_at", "updated_at", "expires_at"},
        "owner_field": None,
        "enum_fields": {"recording_status": RecordingStatus},
    },
}

ALIAS_KEYS = {
    "recordings": "cloud_recordings",
    "marketplace": "marketplace_items",
}


def _coerce_enum(enum_cls, value):
    if value is None or isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for member in enum_cls:
            if member.value == normalized:
                return member
    return enum_cls(value)


def _normalize_payload(config: Dict[str, Any], payload: Dict[str, Any], current_user_id: str, is_create: bool) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    allowed_fields = config["fields"]
    enum_fields = config.get("enum_fields", {})
    owner_field = config.get("owner_field")

    for field in allowed_fields:
        if field in payload:
            value = payload[field]
            if field in enum_fields and value is not None:
                value = _coerce_enum(enum_fields[field], value)
            normalized[field] = value

    if is_create and owner_field and not normalized.get(owner_field):
        normalized[owner_field] = current_user_id

    return normalized


def _upsert_entity(entity_name: str, payload: Dict[str, Any], db: Session, current_user_id: str):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail=f"بيانات {entity_name} غير صالحة")

    config = ENTITY_CONFIG[entity_name]
    model: Type = config["model"]
    entity_id = payload.get("id")
    entity = db.query(model).filter(model.id == entity_id).first() if entity_id else None

    normalized = _normalize_payload(config, payload, current_user_id, is_create=entity is None)

    if entity is None:
        entity = model(**normalized)
        if entity_id:
            entity.id = entity_id
        db.add(entity)
    else:
        for field, value in normalized.items():
            setattr(entity, field, value)

    return entity


def _delete_entity(entity_name: str, entity_id: str, db: Session):
    config = ENTITY_CONFIG[entity_name]
    model: Type = config["model"]
    entity = db.query(model).filter(model.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"العنصر المطلوب في {entity_name} غير موجود")
    db.delete(entity)


def _serialize_sync_payload(current_user_id: str, db: Session) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    posts = (
        db.query(Post)
        .filter((Post.user_id == current_user_id) | (Post.group_id.isnot(None)))
        .order_by(Post.created_at.desc())
        .limit(50)
        .all()
    )
    comments = (
        db.query(Comment)
        .join(Post, Comment.post_id == Post.id)
        .filter((Post.user_id == current_user_id) | (Post.group_id.isnot(None)))
        .order_by(Comment.created_at.desc())
        .limit(100)
        .all()
    )
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user_id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    users = db.query(User).order_by(User.updated_at.desc()).limit(100).all()
    marketplace_items = db.query(MarketplaceItem).order_by(MarketplaceItem.created_at.desc()).limit(20).all()
    tasks = db.query(SharedTask).filter(SharedTask.assigned_to == current_user_id).all()
    stories = (
        db.query(Story)
        .filter(Story.user_id == current_user_id)
        .order_by(Story.created_at.desc())
        .limit(20)
        .all()
    )
    recordings = (
        db.query(CloudRecording)
        .join(LiveStream, CloudRecording.live_stream_id == LiveStream.id)
        .filter(LiveStream.host_id == current_user_id)
        .order_by(CloudRecording.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "profile": schemas.UserDetailResponse.model_validate(user, from_attributes=True).model_dump(mode="json"),
            "users": [schemas.UserDetailResponse.model_validate(item, from_attributes=True).model_dump(mode="json") for item in users],
            "posts": [schemas.PostResponse.model_validate(p, from_attributes=True).model_dump(mode="json") for p in posts],
            "comments": [schemas.CommentResponse.model_validate(comment, from_attributes=True).model_dump(mode="json") for comment in comments],
            "groups": [schemas.GroupResponse.model_validate(g, from_attributes=True).model_dump(mode="json") for g in user.groups],
            "notifications": [schemas.NotificationResponse.model_validate(n, from_attributes=True).model_dump(mode="json") for n in notifications],
            "marketplace_items": [schemas.MarketplaceItemResponse.model_validate(item, from_attributes=True).model_dump(mode="json") for item in marketplace_items],
            "tasks": [schemas.TaskResponse.model_validate(t, from_attributes=True).model_dump(mode="json") for t in tasks],
            "stories": [schemas.StoryResponse.model_validate(story, from_attributes=True).model_dump(mode="json") for story in stories],
            "recordings": [schemas.CloudRecordingResponse.model_validate(recording, from_attributes=True).model_dump(mode="json") for recording in recordings],
        }
    }


@router.get("/all-data/", response_model=Dict[str, Any])
async def sync_all_data(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    مزامنة جميع البيانات المتعلقة بالمستخدم في طلب واحد.
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")
    return _serialize_sync_payload(current_user_id, db)


@router.post("/push")
async def push_local_data(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    استقبال البيانات المحلية من التطبيق ومزامنتها مع السحابة.
    يدعم رفع قوائم كيانات متعددة في نفس الطلب.
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    processed: Dict[str, int] = {}

    for raw_key, items in data.items():
        entity_name = ALIAS_KEYS.get(raw_key, raw_key)
        if entity_name not in ENTITY_CONFIG or not isinstance(items, list):
            continue

        processed[entity_name] = 0
        for item in items:
            _upsert_entity(entity_name, item, db, current_user_id)
            processed[entity_name] += 1

    db.commit()

    return {
        "success": True,
        "message": "تمت مزامنة البيانات المحلية بنجاح",
        "processed": processed,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/batch-operations")
async def batch_operations(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    تنفيذ مجموعة عمليات إنشاء/تحديث/حذف في طلب واحد.
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    operations = payload.get("operations", [])
    if not isinstance(operations, list):
        raise HTTPException(status_code=400, detail="operations يجب أن تكون قائمة")

    processed_results: List[Dict[str, Any]] = []

    for index, operation in enumerate(operations):
        entity_name = ALIAS_KEYS.get(operation.get("entity"), operation.get("entity"))
        action = (operation.get("action") or "").lower()

        if entity_name not in ENTITY_CONFIG:
            raise HTTPException(status_code=400, detail=f"كيان غير مدعوم في العملية رقم {index + 1}")

        if action in {"create", "update", "upsert"}:
            entity = _upsert_entity(entity_name, operation.get("data") or {}, db, current_user_id)
            processed_results.append({
                "entity": entity_name,
                "action": action,
                "id": getattr(entity, "id", None),
                "status": "ok",
            })
        elif action == "delete":
            entity_id = operation.get("id") or (operation.get("data") or {}).get("id")
            if not entity_id:
                raise HTTPException(status_code=400, detail=f"معرف الحذف مفقود في العملية رقم {index + 1}")
            _delete_entity(entity_name, entity_id, db)
            processed_results.append({
                "entity": entity_name,
                "action": action,
                "id": entity_id,
                "status": "ok",
            })
        else:
            raise HTTPException(status_code=400, detail=f"نوع العملية غير مدعوم في العملية رقم {index + 1}")

    db.commit()

    return {
        "success": True,
        "processed_count": len(processed_results),
        "results": processed_results,
        "message": f"تمت معالجة {len(processed_results)} عملية بنجاح",
        "timestamp": datetime.utcnow().isoformat(),
    }
