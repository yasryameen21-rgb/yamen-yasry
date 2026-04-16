from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
import json
from datetime import datetime

from database import get_db
from models import LiveStream, LiveStreamStatus, Message, MessageType, Conversation, CloudRecording, RecordingStatus
from schemas import LiveStreamCreate, LiveStreamUpdate, LiveStreamResponse, SignalingMessage
from security import get_current_user
router = APIRouter(prefix="/api/live", tags=["Live Video"])

# إدارة اتصالات WebSocket
class ConnectionManager:
    def __init__(self):
        # user_id -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # stream_id -> list of user_ids
        self.stream_viewers: Dict[str, List[str]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            # إزالة المستخدم من جميع غرف البث
            for stream_id in self.stream_viewers:
                if user_id in self.stream_viewers[stream_id]:
                    self.stream_viewers[stream_id].remove(user_id)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_stream(self, stream_id: str, message: dict):
        if stream_id in self.stream_viewers:
            for user_id in self.stream_viewers[stream_id]:
                await self.send_personal_message(message, user_id)

manager = ConnectionManager()

@router.get("", response_model=List[LiveStreamResponse])
async def list_live_streams(
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(LiveStream)
    if status:
        query = query.filter(LiveStream.status == status)
    return query.order_by(LiveStream.started_at.desc()).offset(skip).limit(limit).all()

@router.post("/start", response_model=LiveStreamResponse)
async def start_live_stream(
    stream_data: LiveStreamCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    # إنشاء البث
    new_stream = LiveStream(
        host_id=current_user_id,
        conversation_id=stream_data.conversation_id,
        title=stream_data.title,
        sdp_offer=stream_data.sdp_offer,
        status=LiveStreamStatus.LIVE
    )
    db.add(new_stream)
    
    # إضافة رسالة في المحادثة تفيد ببدء البث
    if stream_data.conversation_id:
        new_message = Message(
            conversation_id=stream_data.conversation_id,
            sender_id=current_user_id,
            content=f"بدأ {current_user_id} بثاً مباشراً",
            message_type=MessageType.LIVE_STARTED
        )
        db.add(new_message)
    
    db.commit()
    db.refresh(new_stream)
    return new_stream

@router.get("/{stream_id}", response_model=LiveStreamResponse)
async def get_live_stream(
    stream_id: str,
    db: Session = Depends(get_db)
):
    stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="البث غير موجود")
    return stream

@router.post("/{stream_id}/end", response_model=LiveStreamResponse)
async def end_live_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="البث غير موجود")
    
    if stream.host_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية إنهاء هذا البث")
    
    stream.status = LiveStreamStatus.ENDED
    stream.ended_at = datetime.utcnow()
    
    # تحديث حالة التسجيل إذا كان مفعلاً
    if stream.is_recording_enabled:
        stream.recording_status = RecordingStatus.PROCESSING
    
    # إضافة رسالة انتهاء البث
    if stream.conversation_id:
        new_message = Message(
            conversation_id=stream.conversation_id,
            sender_id=current_user_id,
            content="انتهى البث المباشر",
            message_type=MessageType.LIVE_ENDED
        )
        db.add(new_message)
        
    db.commit()
    db.refresh(stream)
    
    # إبلاغ المشاهدين بانتهاء البث عبر WebSocket
    await manager.broadcast_to_stream(stream_id, {"type": "live_ended", "stream_id": stream_id})
    
    return stream

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # معالجة أنواع الرسائل المختلفة
            msg_type = message.get("type")
            
            if msg_type == "join_stream":
                stream_id = message.get("stream_id")
                if stream_id not in manager.stream_viewers:
                    manager.stream_viewers[stream_id] = []
                if user_id not in manager.stream_viewers[stream_id]:
                    manager.stream_viewers[stream_id].append(user_id)
                
                # إبلاغ المضيف بانضمام مشاهد جديد (اختياري)
                # يمكن تحديث عدد المشاهدين في قاعدة البيانات هنا
                
            elif msg_type == "signaling":
                # إعادة توجيه رسائل WebRTC Signaling (Offer, Answer, Candidate)
                target_id = message.get("target_id")
                if target_id:
                    await manager.send_personal_message(message, target_id)
                    
            elif msg_type == "comment":
                # بث التعليقات لجميع مشاهدي البث
                stream_id = message.get("stream_id")
                await manager.broadcast_to_stream(stream_id, {
                    "type": "new_comment",
                    "user_id": user_id,
                    "content": message.get("content"),
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
