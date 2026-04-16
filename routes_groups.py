"""
مسارات المجموعات
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Group, User
from schemas import GroupCreate, GroupUpdate, GroupResponse
from security import get_current_user

router = APIRouter(prefix="/api/groups", tags=["Groups"])


@router.get("", response_model=List[GroupResponse])
async def list_groups(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return db.query(Group).order_by(Group.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")
    return group


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    admin = db.query(User).filter(User.id == current_user_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    group = Group(
        name=data.name,
        description=data.description,
        group_type=data.group_type,
        admin_id=current_user_id,
        group_image_url=data.group_image_url,
    )
    group.members.append(admin)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")
    if group.admin_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية تعديل هذه المجموعة")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    group = db.query(Group).filter(Group.id == group_id).first()
    user = db.query(User).filter(User.id == current_user_id).first()
    if not group or not user:
        raise HTTPException(status_code=404, detail="المجموعة أو المستخدم غير موجود")

    if user not in group.members:
        group.members.append(user)
        db.commit()

    return {"success": True, "message": "تم الانضمام إلى المجموعة بنجاح"}


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    group = db.query(Group).filter(Group.id == group_id).first()
    user = db.query(User).filter(User.id == current_user_id).first()
    if not group or not user:
        raise HTTPException(status_code=404, detail="المجموعة أو المستخدم غير موجود")

    if group.admin_id == current_user_id:
        raise HTTPException(status_code=400, detail="لا يمكن للمشرف مغادرة المجموعة قبل نقل الإدارة")

    if user in group.members:
        group.members.remove(user)
        db.commit()

    return {"success": True, "message": "تمت مغادرة المجموعة بنجاح"}
