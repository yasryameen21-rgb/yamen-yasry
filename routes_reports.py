"""
مسارات البلاغات والإشراف
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ContentReport, LiveStream, ReportStatus, User, Comment, Post
from schemas import ReportCreate, ReportResponse, ReportStatusUpdate
from security import get_current_user as get_current_user_id

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _require_auth(current_user_id: str | None) -> str:
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")
    return current_user_id


def _get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return user


def _assert_target_exists(db: Session, target_type: str, target_id: str):
    model_map = {
        "post": Post,
        "comment": Comment,
        "user": User,
        "live": LiveStream,
    }
    model = model_map.get(target_type)
    if not model:
        raise HTTPException(status_code=400, detail="نوع البلاغ غير مدعوم")
    item = db.query(model).filter(model.id == target_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="العنصر المُبلّغ عنه غير موجود")


@router.post("", response_model=ReportResponse)
async def create_report(
    payload: ReportCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _get_user_or_404(db, current_user_id)
    _assert_target_exists(db, payload.target_type, payload.target_id)

    report = ContentReport(
        reporter_id=current_user_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        details=payload.details,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/mine", response_model=list[ReportResponse])
async def get_my_reports(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    return db.query(ContentReport).filter(
        ContentReport.reporter_id == current_user_id
    ).order_by(ContentReport.created_at.desc()).all()


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    status: str | None = None,
    target_type: str | None = None,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    user = _get_user_or_404(db, current_user_id)
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="هذه الميزة للمشرفين فقط")

    query = db.query(ContentReport)
    if status:
        query = query.filter(ContentReport.status == status)
    if target_type:
        query = query.filter(ContentReport.target_type == target_type)
    return query.order_by(ContentReport.created_at.desc()).all()


@router.post("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: str,
    payload: ReportStatusUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    user = _get_user_or_404(db, current_user_id)
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="هذه الميزة للمشرفين فقط")

    report = db.query(ContentReport).filter(ContentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="البلاغ غير موجود")

    report.status = payload.status
    db.commit()
    db.refresh(report)
    return report
