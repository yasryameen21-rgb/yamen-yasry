"""
محولات توافق العقود بين SQLAlchemy وواجهات التطبيق.
تعيد بيانات JSON بصيغة camelCase المتوافقة مع نماذج الموبايل.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def serialize_user(user) -> Dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phoneNumber": user.phone_number,
        "role": (_enum_value(user.role) or "user").capitalize(),
        "profileImageUrl": user.profile_image_url,
        "coverImageUrl": user.cover_image_url,
        "bio": user.bio,
        "isVerified": bool(user.is_verified),
        "isBanned": bool(user.is_banned),
        "isMutedFromCommenting": bool(getattr(user, "is_muted_from_commenting", False)),
        "isMutedFromPosting": bool(getattr(user, "is_muted_from_posting", False)),
        "groupIds": [group.id for group in getattr(user, "groups", [])],
        "friendIds": [friend.id for friend in getattr(user, "friends", [])],
        "darkModeEnabled": bool(getattr(user, "dark_mode_enabled", False)),
        "primaryColor": getattr(user, "primary_color", "#2196F3"),
        "publicKey": getattr(user, "public_key", None),
        "encryptedPrivateKey": getattr(user, "encrypted_private_key", None),
        "lastLogin": user.last_login.isoformat() if user.last_login else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
    }


def serialize_comment(comment) -> Dict[str, Any]:
    author = getattr(comment, "author", None)
    return {
        "id": comment.id,
        "postId": comment.post_id,
        "userId": comment.user_id,
        "userName": getattr(author, "name", None),
        "userProfileImage": getattr(author, "profile_image_url", None),
        "content": comment.content,
        "reactions": comment.reactions or {},
        "createdAt": comment.created_at.isoformat() if comment.created_at else None,
        "updatedAt": comment.updated_at.isoformat() if comment.updated_at else None,
    }


def serialize_post(post) -> Dict[str, Any]:
    author = getattr(post, "author", None)
    reactions = post.reactions or {}
    liked_by = reactions.get("like", []) if isinstance(reactions, dict) else []
    return {
        "id": post.id,
        "userId": post.user_id,
        "userName": getattr(author, "name", None),
        "userProfileImage": getattr(author, "profile_image_url", None),
        "content": post.content,
        "mediaUrl": post.media_url,
        "type": (_enum_value(post.post_type) or "text").capitalize(),
        "createdAt": post.created_at.isoformat() if post.created_at else None,
        "updatedAt": post.updated_at.isoformat() if post.updated_at else None,
        "likesCount": len(liked_by),
        "likedByUsers": liked_by,
        "groupId": post.group_id,
        "comments": [serialize_comment(comment) for comment in getattr(post, "comments", [])],
        "isHidden": bool(post.is_hidden),
        "reactions": reactions,
        "linkPreviewUrl": post.link_preview_url,
        "linkPreviewTitle": post.link_preview_title,
        "linkPreviewDescription": post.link_preview_description,
        "linkPreviewImage": post.link_preview_image,
        "sharesCount": post.shares_count,
        "username": getattr(author, "name", None),
    }


def serialize_task(task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "groupId": task.group_id,
        "createdBy": task.created_by,
        "assignedTo": task.assigned_to,
        "dueDate": task.due_date.isoformat() if task.due_date else None,
        "status": _enum_value(task.status),
        "priority": task.priority,
        "createdAt": task.created_at.isoformat() if task.created_at else None,
        "updatedAt": task.updated_at.isoformat() if task.updated_at else None,
    }


def serialize_notification(notification) -> Dict[str, Any]:
    return {
        "id": notification.id,
        "userId": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "type": (_enum_value(notification.notification_type) or "system").title().replace("_", ""),
        "relatedId": notification.related_id,
        "createdAt": notification.created_at.isoformat() if notification.created_at else None,
        "isRead": bool(notification.is_read),
        "updatedAt": notification.updated_at.isoformat() if notification.updated_at else None,
    }


def serialize_group(group) -> Dict[str, Any]:
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "type": (_enum_value(group.group_type) or "custom").capitalize(),
        "privacy": (_enum_value(group.privacy) or "public").capitalize(),
        "adminId": group.admin_id,
        "memberIds": [member.id for member in getattr(group, "members", [])],
        "groupImageUrl": group.group_image_url,
        "coverImageUrl": group.cover_image_url,
        "createdAt": group.created_at.isoformat() if group.created_at else None,
    }


def serialize_story(story) -> Dict[str, Any]:
    author = getattr(story, "author", None)
    viewed_by = getattr(story, "viewed_by_users", []) or []
    return {
        "id": story.id,
        "userId": story.user_id,
        "userName": getattr(author, "name", None),
        "userProfileImage": getattr(author, "profile_image_url", None),
        "mediaUrl": story.media_url,
        "mediaType": story.media_type,
        "createdAt": story.created_at.isoformat() if story.created_at else None,
        "expiresAt": story.expires_at.isoformat() if story.expires_at else None,
        "viewedByUsers": viewed_by,
    }


def serialize_recording(recording) -> Dict[str, Any]:
    live_stream = getattr(recording, "live_stream", None)
    return {
        "id": recording.id,
        "liveStreamId": recording.live_stream_id,
        "userId": getattr(live_stream, "host_id", None),
        "title": recording.title,
        "description": recording.description,
        "videoUrl": recording.video_url,
        "thumbnailUrl": recording.thumbnail_url,
        "durationSeconds": recording.duration_seconds,
        "fileSizeMb": recording.file_size_mb,
        "videoQuality": recording.video_quality,
        "recordingStatus": _enum_value(recording.recording_status),
        "viewCount": recording.view_count,
        "isPublic": bool(recording.is_public),
        "allowedViewers": recording.allowed_viewers or [],
        "createdAt": recording.created_at.isoformat() if recording.created_at else None,
        "updatedAt": recording.updated_at.isoformat() if recording.updated_at else None,
        "expiresAt": recording.expires_at.isoformat() if recording.expires_at else None,
    }


def serialize_message(message) -> Dict[str, Any]:
    sender = getattr(message, "sender", None)
    return {
        "id": message.id,
        "senderId": message.sender_id,
        "senderName": getattr(sender, "name", None),
        "senderProfileImage": getattr(sender, "profile_image_url", None),
        "conversationId": message.conversation_id,
        "content": message.content,
        "type": (_enum_value(message.message_type) or "text").replace("_", " ").title().replace(" ", ""),
        "mediaUrl": message.media_url,
        "createdAt": message.created_at.isoformat() if message.created_at else None,
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
        "reactions": message.reactions or {},
        "isRead": bool(message.is_read),
        "replyToMessageId": message.reply_to_message_id,
        "isEncrypted": bool(message.is_encrypted),
        "encryptionV": message.encryption_v,
    }


def serialize_marketplace_item(item) -> Dict[str, Any]:
    seller = getattr(item, "seller", None)
    return {
        "id": item.id,
        "sellerId": item.seller_id,
        "sellerName": getattr(seller, "name", None),
        "groupId": item.group_id,
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "currency": item.currency,
        "category": (_enum_value(item.category) or "other").replace("_", " ").title().replace(" ", ""),
        "status": (_enum_value(item.status) or "available").capitalize(),
        "location": item.location,
        "imageUrls": item.image_urls or [],
        "createdAt": item.created_at.isoformat() if item.created_at else None,
    }


def serialize_snapshot(*, posts, users, groups, notifications, marketplace_items, tasks, stories=None, recordings=None, messages=None) -> Dict[str, Any]:
    return {
        "posts": [serialize_post(post) for post in posts],
        "comments": [serialize_comment(comment) for post in posts for comment in getattr(post, "comments", [])],
        "messages": [serialize_message(message) for message in (messages or [])],
        "tasks": [serialize_task(task) for task in tasks],
        "users": [serialize_user(user) for user in users],
        "stories": [serialize_story(story) for story in (stories or [])],
        "notifications": [serialize_notification(notification) for notification in notifications],
        "recordings": [serialize_recording(recording) for recording in (recordings or [])],
        "groups": [serialize_group(group) for group in groups],
        "marketplaceItems": [serialize_marketplace_item(item) for item in marketplace_items],
    }
