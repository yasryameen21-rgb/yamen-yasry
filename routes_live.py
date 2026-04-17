from datetime import datetime
from typing import Dict, List
import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import (
    LiveJoinRequest,
    LiveRequestStatus,
    LiveStream,
    LiveStreamStatus,
    Message,
    MessageType,
)
from schemas import (
    LiveJoinRequestCreate,
    LiveJoinRequestResponse,
    LiveStreamCreate,
    LiveStreamResponse,
    LiveStreamStatsResponse,
)
from security import get_current_user as get_current_user_id

router = APIRouter(prefix="/api/live", tags=["Live Video"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.stream_viewers: Dict[str, List[str]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def _sync_viewer_count(self, stream_id: str):
        db = SessionLocal()
        try:
            stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
            if stream:
                viewers = len(self.stream_viewers.get(stream_id, []))
                stream.viewer_count = viewers
                stream.peak_viewer_count = max(stream.peak_viewer_count or 0, viewers)
                db.commit()
        finally:
            db.close()

    def register_stream_viewer(self, stream_id: str, user_id: str):
        viewers = self.stream_viewers.setdefault(stream_id, [])
        if user_id not in viewers:
            viewers.append(user_id)
            self._sync_viewer_count(stream_id)

    def unregister_stream_viewer(self, stream_id: str, user_id: str):
        viewers = self.stream_viewers.get(stream_id, [])
        if user_id in viewers:
            viewers.remove(user_id)
            self._sync_viewer_count(stream_id)

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        for stream_id in list(self.stream_viewers.keys()):
            self.unregister_stream_viewer(stream_id, user_id)
            if not self.stream_viewers.get(stream_id):
                self.stream_viewers.pop(stream_id, None)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_stream(self, stream_id: str, message: dict):
        if stream_id in self.stream_viewers:
            for user_id in self.stream_viewers[stream_id]:
                await self.send_personal_message(message, user_id)


manager = ConnectionManager()


def _require_auth(current_user_id: str | None) -> str:
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    return current_user_id


def _get_stream_or_404(db: Session, stream_id: str) -> LiveStream:
    stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="البث غير موجود")
    return stream


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
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)

    new_stream = LiveStream(
        host_id=current_user_id,
        conversation_id=stream_data.conversation_id,
        title=stream_data.title,
        sdp_offer=stream_data.sdp_offer,
        status=LiveStreamStatus.LIVE,
    )
    db.add(new_stream)

    if stream_data.conversation_id:
        db.add(Message(
            conversation_id=stream_data.conversation_id,
            sender_id=current_user_id,
            content=f"بدأ {current_user_id} بثاً مباشراً",
            message_type=MessageType.LIVE_STARTED,
        ))

    db.commit()
    db.refresh(new_stream)
    return new_stream


@router.get("/{stream_id}", response_model=LiveStreamResponse)
async def get_live_stream(stream_id: str, db: Session = Depends(get_db)):
    return _get_stream_or_404(db, stream_id)


@router.get("/{stream_id}/stats", response_model=LiveStreamStatsResponse)
async def get_live_stream_stats(stream_id: str, db: Session = Depends(get_db)):
    stream = _get_stream_or_404(db, stream_id)
    pending = db.query(LiveJoinRequest).filter(
        LiveJoinRequest.stream_id == stream_id,
        LiveJoinRequest.status == LiveRequestStatus.PENDING,
    ).count()
    approved = db.query(LiveJoinRequest).filter(
        LiveJoinRequest.stream_id == stream_id,
        LiveJoinRequest.status == LiveRequestStatus.APPROVED,
    ).count()
    rejected = db.query(LiveJoinRequest).filter(
        LiveJoinRequest.stream_id == stream_id,
        LiveJoinRequest.status == LiveRequestStatus.REJECTED,
    ).count()
    return {
        "stream_id": stream.id,
        "viewer_count": stream.viewer_count or 0,
        "peak_viewer_count": stream.peak_viewer_count or 0,
        "pending_join_requests": pending,
        "approved_join_requests": approved,
        "rejected_join_requests": rejected,
    }


@router.post("/{stream_id}/join-requests", response_model=LiveJoinRequestResponse)
async def request_join_live_stream(
    stream_id: str,
    payload: LiveJoinRequestCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)
    stream = _get_stream_or_404(db, stream_id)

    if stream.host_id == current_user_id:
        raise HTTPException(status_code=400, detail="أنت المضيف بالفعل")

    existing = db.query(LiveJoinRequest).filter(
        LiveJoinRequest.stream_id == stream_id,
        LiveJoinRequest.requester_id == current_user_id,
    ).first()

    if existing and existing.status == LiveRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="يوجد طلب بث معلّق بالفعل")

    if existing:
        existing.note = payload.note
        existing.status = LiveRequestStatus.PENDING
        existing.responded_at = None
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    request_item = LiveJoinRequest(
        stream_id=stream_id,
        requester_id=current_user_id,
        note=payload.note,
        status=LiveRequestStatus.PENDING,
    )
    db.add(request_item)
    db.commit()
    db.refresh(request_item)

    await manager.send_personal_message(
        {
            "type": "live_join_request",
            "stream_id": stream_id,
            "request_id": request_item.id,
            "requester_id": current_user_id,
            "note": payload.note,
        },
        stream.host_id,
    )
    return request_item


@router.get("/{stream_id}/join-requests", response_model=List[LiveJoinRequestResponse])
async def list_join_requests(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)
    stream = _get_stream_or_404(db, stream_id)
    if stream.host_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية عرض طلبات هذا البث")

    return db.query(LiveJoinRequest).filter(
        LiveJoinRequest.stream_id == stream_id
    ).order_by(LiveJoinRequest.created_at.desc()).all()


@router.post("/join-requests/{request_id}/approve", response_model=LiveJoinRequestResponse)
async def approve_join_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)
    request_item = db.query(LiveJoinRequest).filter(LiveJoinRequest.id == request_id).first()
    if not request_item:
        raise HTTPException(status_code=404, detail="طلب البث غير موجود")

    stream = _get_stream_or_404(db, request_item.stream_id)
    if stream.host_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية الموافقة على هذا الطلب")

    request_item.status = LiveRequestStatus.APPROVED
    request_item.responded_at = datetime.utcnow()
    request_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request_item)

    await manager.send_personal_message(
        {
            "type": "live_join_request_approved",
            "stream_id": request_item.stream_id,
            "request_id": request_item.id,
        },
        request_item.requester_id,
    )
    return request_item


@router.post("/join-requests/{request_id}/reject", response_model=LiveJoinRequestResponse)
async def reject_join_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)
    request_item = db.query(LiveJoinRequest).filter(LiveJoinRequest.id == request_id).first()
    if not request_item:
        raise HTTPException(status_code=404, detail="طلب البث غير موجود")

    stream = _get_stream_or_404(db, request_item.stream_id)
    if stream.host_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية رفض هذا الطلب")

    request_item.status = LiveRequestStatus.REJECTED
    request_item.responded_at = datetime.utcnow()
    request_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request_item)

    await manager.send_personal_message(
        {
            "type": "live_join_request_rejected",
            "stream_id": request_item.stream_id,
            "request_id": request_item.id,
        },
        request_item.requester_id,
    )
    return request_item


@router.post("/{stream_id}/end", response_model=LiveStreamResponse)
async def end_live_stream(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    current_user_id = _require_auth(current_user_id)
    stream = _get_stream_or_404(db, stream_id)

    if stream.host_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية إنهاء هذا البث")

    stream.status = LiveStreamStatus.ENDED
    stream.ended_at = datetime.utcnow()

    if stream.is_recording_enabled:
        stream.recording_status = "processing"

    if stream.conversation_id:
        db.add(Message(
            conversation_id=stream.conversation_id,
            sender_id=current_user_id,
            content="انتهى البث المباشر",
            message_type=MessageType.LIVE_ENDED,
        ))

    db.commit()
    db.refresh(stream)
    await manager.broadcast_to_stream(stream_id, {"type": "live_ended", "stream_id": stream_id})
    return stream


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "join_stream":
                stream_id = message.get("stream_id")
                if stream_id:
                    manager.register_stream_viewer(stream_id, user_id)
                    await manager.broadcast_to_stream(stream_id, {
                        "type": "viewer_count_updated",
                        "stream_id": stream_id,
                        "viewer_count": len(manager.stream_viewers.get(stream_id, [])),
                    })

            elif msg_type == "leave_stream":
                stream_id = message.get("stream_id")
                if stream_id:
                    manager.unregister_stream_viewer(stream_id, user_id)

            elif msg_type == "signaling":
                target_id = message.get("target_id")
                if target_id:
                    await manager.send_personal_message(message, target_id)

            elif msg_type == "comment":
                stream_id = message.get("stream_id")
                if stream_id:
                    await manager.broadcast_to_stream(stream_id, {
                        "type": "new_comment",
                        "user_id": user_id,
                        "content": message.get("content"),
                        "timestamp": datetime.utcnow().isoformat(),
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
