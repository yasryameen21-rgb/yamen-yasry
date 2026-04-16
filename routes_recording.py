"""
مسارات إدارة تسجيل البث السحابي (Cloud Recording) والفيديو عند الطلب (VOD)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database import get_db
from models import CloudRecording, LiveStream, RecordingStatus, LiveStreamStatus, User
from schemas import (
    CloudRecordingCreate,
    CloudRecordingUpdate,
    CloudRecordingResponse,
    LiveStreamResponse
)
from security import get_current_user

router = APIRouter(prefix="/api/recordings", tags=["Cloud Recording & VOD"])


# ==================== إنشاء وإدارة التسجيلات ====================

@router.post("/", response_model=CloudRecordingResponse)
async def create_recording(
    recording_data: CloudRecordingCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    إنشاء تسجيل جديد للبث المباشر
    - التحقق من أن البث موجود وملك للمستخدم الحالي
    - حفظ معلومات التسجيل في قاعدة البيانات
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    # التحقق من وجود البث
    live_stream = db.query(LiveStream).filter(
        LiveStream.id == recording_data.live_stream_id
    ).first()
    
    if not live_stream:
        raise HTTPException(status_code=404, detail="البث المباشر غير موجود")
    
    # التحقق من أن المستخدم هو صاحب البث
    if live_stream.host_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="لا تملك صلاحية إنشاء تسجيل لهذا البث"
        )
    
    # إنشاء التسجيل الجديد
    new_recording = CloudRecording(
        id=str(uuid.uuid4()),
        live_stream_id=recording_data.live_stream_id,
        title=recording_data.title,
        description=recording_data.description,
        video_url=recording_data.video_url,
        thumbnail_url=recording_data.thumbnail_url,
        duration_seconds=recording_data.duration_seconds,
        file_size_mb=recording_data.file_size_mb,
        video_quality=recording_data.video_quality,
        is_public=recording_data.is_public,
        allowed_viewers=recording_data.allowed_viewers,
        expires_at=recording_data.expires_at,
        recording_status=RecordingStatus.COMPLETED,
        view_count=0
    )
    
    # تحديث معلومات البث بمعلومات التسجيل
    live_stream.recording_url = recording_data.video_url
    live_stream.thumbnail_url = recording_data.thumbnail_url
    live_stream.recording_duration = recording_data.duration_seconds
    live_stream.recording_size_mb = recording_data.file_size_mb
    live_stream.recording_status = RecordingStatus.COMPLETED
    live_stream.recording_completed_at = datetime.utcnow()
    
    db.add(new_recording)
    db.commit()
    db.refresh(new_recording)
    
    return new_recording


@router.get("/{recording_id}", response_model=CloudRecordingResponse)
async def get_recording(
    recording_id: str,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    """
    الحصول على معلومات تسجيل محدد
    - التحقق من الخصوصية والصلاحيات
    - زيادة عدد المشاهدات
    """
    recording = db.query(CloudRecording).filter(
        CloudRecording.id == recording_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")
    
    # التحقق من الخصوصية
    if not recording.is_public:
        if not current_user_id:
            raise HTTPException(
                status_code=403,
                detail="هذا التسجيل خاص ولا يمكن الوصول إليه"
            )
        
        # التحقق من أن المستخدم مصرح له بالمشاهدة
        live_stream = db.query(LiveStream).filter(
            LiveStream.id == recording.live_stream_id
        ).first()
        
        if live_stream.host_id != current_user_id and current_user_id not in recording.allowed_viewers:
            raise HTTPException(
                status_code=403,
                detail="لا تملك صلاحية مشاهدة هذا التسجيل"
            )
    
    # التحقق من انتهاء صلاحية التسجيل
    if recording.expires_at and recording.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=410,
            detail="انتهت صلاحية هذا التسجيل"
        )
    
    # زيادة عدد المشاهدات
    recording.view_count += 1
    db.commit()
    db.refresh(recording)
    
    return recording


@router.get("/", response_model=List[CloudRecordingResponse])
async def list_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    live_stream_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    """
    الحصول على قائمة التسجيلات
    - تصفية حسب البث المباشر
    - تصفية حسب الخصوصية
    - دعم الترقيم (Pagination)
    """
    query = db.query(CloudRecording)
    
    # تصفية حسب البث المباشر
    if live_stream_id:
        query = query.filter(CloudRecording.live_stream_id == live_stream_id)
    
    # تصفية حسب الخصوصية
    if is_public is not None:
        query = query.filter(CloudRecording.is_public == is_public)
    else:
        # إذا لم يتم تحديد الخصوصية، عرض التسجيلات العامة فقط
        # أو التسجيلات الخاصة التي يملكها المستخدم أو مصرح له بمشاهدتها
        if current_user_id:
            # للمستخدمين المسجلين: عرض التسجيلات العامة والخاصة المسموح لهم بمشاهدتها
            query = query.filter(
                (CloudRecording.is_public == True) |
                (CloudRecording.allowed_viewers.contains(current_user_id))
            )
        else:
            # للمستخدمين غير المسجلين: عرض التسجيلات العامة فقط
            query = query.filter(CloudRecording.is_public == True)
    
    # حساب إجمالي النتائج
    total = query.count()
    
    # تطبيق الترقيم
    recordings = query.order_by(CloudRecording.created_at.desc()).offset(skip).limit(limit).all()
    
    return recordings


@router.put("/{recording_id}", response_model=CloudRecordingResponse)
async def update_recording(
    recording_id: str,
    recording_data: CloudRecordingUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    تحديث معلومات التسجيل
    - التحقق من أن المستخدم هو صاحب البث
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    recording = db.query(CloudRecording).filter(
        CloudRecording.id == recording_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")
    
    # التحقق من الصلاحيات
    live_stream = db.query(LiveStream).filter(
        LiveStream.id == recording.live_stream_id
    ).first()
    
    if live_stream.host_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="لا تملك صلاحية تعديل هذا التسجيل"
        )
    
    # تحديث البيانات
    if recording_data.title is not None:
        recording.title = recording_data.title
    if recording_data.description is not None:
        recording.description = recording_data.description
    if recording_data.is_public is not None:
        recording.is_public = recording_data.is_public
    if recording_data.allowed_viewers is not None:
        recording.allowed_viewers = recording_data.allowed_viewers
    if recording_data.expires_at is not None:
        recording.expires_at = recording_data.expires_at
    
    recording.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(recording)
    
    return recording


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    حذف تسجيل
    - التحقق من أن المستخدم هو صاحب البث
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    recording = db.query(CloudRecording).filter(
        CloudRecording.id == recording_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")
    
    # التحقق من الصلاحيات
    live_stream = db.query(LiveStream).filter(
        LiveStream.id == recording.live_stream_id
    ).first()
    
    if live_stream.host_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="لا تملك صلاحية حذف هذا التسجيل"
        )
    
    db.delete(recording)
    
    # تحديث معلومات البث
    live_stream.recording_url = None
    live_stream.thumbnail_url = None
    live_stream.recording_status = None
    
    db.commit()
    
    return {"success": True, "message": "تم حذف التسجيل بنجاح"}


# ==================== البث المباشر مع معلومات التسجيل ====================

@router.get("/stream/{stream_id}/recording", response_model=Optional[CloudRecordingResponse])
async def get_stream_recording(
    stream_id: str,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    """
    الحصول على تسجيل البث المباشر المحدد
    """
    live_stream = db.query(LiveStream).filter(
        LiveStream.id == stream_id
    ).first()
    
    if not live_stream:
        raise HTTPException(status_code=404, detail="البث المباشر غير موجود")
    
    # البحث عن التسجيل المرتبط بهذا البث
    recording = db.query(CloudRecording).filter(
        CloudRecording.live_stream_id == stream_id
    ).first()
    
    if not recording:
        return None
    
    # التحقق من الخصوصية
    if not recording.is_public:
        if not current_user_id:
            raise HTTPException(
                status_code=403,
                detail="هذا التسجيل خاص"
            )
        
        if live_stream.host_id != current_user_id and current_user_id not in recording.allowed_viewers:
            raise HTTPException(
                status_code=403,
                detail="لا تملك صلاحية مشاهدة هذا التسجيل"
            )
    
    return recording


@router.get("/user/my-recordings", response_model=List[CloudRecordingResponse])
async def get_my_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    الحصول على جميع تسجيلاتي (البث المباشر الذي سجلته)
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    # الحصول على جميع البث المباشر الذي أنشأه المستخدم
    user_streams = db.query(LiveStream).filter(
        LiveStream.host_id == current_user_id
    ).all()
    
    stream_ids = [stream.id for stream in user_streams]
    
    if not stream_ids:
        return []
    
    # الحصول على التسجيلات المرتبطة بهذه البث
    recordings = db.query(CloudRecording).filter(
        CloudRecording.live_stream_id.in_(stream_ids)
    ).order_by(CloudRecording.created_at.desc()).offset(skip).limit(limit).all()
    
    return recordings


@router.get("/user/watched-recordings", response_model=List[CloudRecordingResponse])
async def get_watched_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    الحصول على التسجيلات التي شاهدتها (التسجيلات المسموح لي بمشاهدتها)
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    # الحصول على التسجيلات العامة أو التسجيلات المسموح لي بمشاهدتها
    recordings = db.query(CloudRecording).filter(
        (CloudRecording.is_public == True) |
        (CloudRecording.allowed_viewers.contains(current_user_id))
    ).order_by(CloudRecording.created_at.desc()).offset(skip).limit(limit).all()
    
    return recordings


# ==================== إحصائيات التسجيلات ====================

@router.get("/{recording_id}/stats")
async def get_recording_stats(
    recording_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    الحصول على إحصائيات التسجيل
    """
    if not current_user_id:
        raise HTTPException(status_code=401, detail="غير مصرح")
    
    recording = db.query(CloudRecording).filter(
        CloudRecording.id == recording_id
    ).first()
    
    if not recording:
        raise HTTPException(status_code=404, detail="التسجيل غير موجود")
    
    # التحقق من الصلاحيات
    live_stream = db.query(LiveStream).filter(
        LiveStream.id == recording.live_stream_id
    ).first()
    
    if live_stream.host_id != current_user_id:
        raise HTTPException(
            status_code=403,
            detail="لا تملك صلاحية عرض إحصائيات هذا التسجيل"
        )
    
    return {
        "recording_id": recording.id,
        "title": recording.title,
        "view_count": recording.view_count,
        "duration_seconds": recording.duration_seconds,
        "file_size_mb": recording.file_size_mb,
        "video_quality": recording.video_quality,
        "created_at": recording.created_at,
        "updated_at": recording.updated_at,
        "is_public": recording.is_public,
        "viewers_count": len(recording.allowed_viewers) if not recording.is_public else "غير محدود"
    }
