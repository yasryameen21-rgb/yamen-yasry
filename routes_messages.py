"""
مسارات المحادثات والرسائل
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Conversation, Message, User
from schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from security import get_current_user

conversation_router = APIRouter(prefix="/api/conversations", tags=["Conversations"])
message_router = APIRouter(prefix="/api/messages", tags=["Messages"])


@conversation_router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    return db.query(Conversation).filter(
        Conversation.participants.any(User.id == current_user_id)
    ).order_by(
        Conversation.last_message_time.desc(),
        Conversation.created_at.desc()
    ).offset(skip).limit(limit).all()


@conversation_router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    participant_ids = list(dict.fromkeys([current_user_id, *data.participant_ids]))
    participants = db.query(User).filter(User.id.in_(participant_ids)).all()
    if len(participants) != len(participant_ids):
        raise HTTPException(status_code=404, detail="يوجد مشاركون غير موجودين")

    conversation = Conversation(
        name=data.name,
        is_group_chat=data.is_group_chat,
        participants=participants,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@conversation_router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")

    if current_user_id and current_user_id not in {participant.id for participant in conversation.participants}:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية الوصول إلى هذه المحادثة")

    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()


@message_router.get("", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    query = db.query(Message)

    if conversation_id:
        query = query.filter(Message.conversation_id == conversation_id)

    if current_user_id:
        query = query.join(Conversation, Message.conversation_id == Conversation.id).filter(
            Conversation.participants.any(User.id == current_user_id)
        )

    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


@message_router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@message_router.post("/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")

    if current_user_id not in {participant.id for participant in conversation.participants}:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية الإرسال في هذه المحادثة")

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user_id,
        content=data.content,
        message_type=data.message_type,
        media_url=data.media_url,
        reply_to_message_id=data.reply_to_message_id,
        is_encrypted=data.is_encrypted,
        encryption_v=data.encryption_v,
    )
    db.add(message)
    conversation.last_message_time = message.created_at
    db.commit()
    db.refresh(message)
    return message


@message_router.put("/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="الرسالة غير موجودة")

    conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if not conversation or current_user_id not in {participant.id for participant in conversation.participants}:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية تعديل هذه الرسالة")

    message.is_read = True
    db.commit()
    return {"success": True, "message": "تم تعليم الرسالة كمقروءة"}
