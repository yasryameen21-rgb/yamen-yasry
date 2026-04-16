"""
مسارات المهام المشتركة
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import SharedTask, Group, User
from schemas import TaskCreate, TaskUpdate, TaskResponse
from security import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    group_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user_id: Optional[str] = Depends(get_current_user)
):
    query = db.query(SharedTask)

    if group_id:
        query = query.filter(SharedTask.group_id == group_id)
    if assigned_to:
        query = query.filter(SharedTask.assigned_to == assigned_to)
    elif current_user_id:
        query = query.filter(
            (SharedTask.assigned_to == current_user_id) |
            (SharedTask.created_by == current_user_id)
        )

    return query.order_by(SharedTask.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(SharedTask).filter(SharedTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    return task


@router.get("/user/{user_id}", response_model=List[TaskResponse])
async def get_user_tasks(
    user_id: str,
    db: Session = Depends(get_db)
):
    return db.query(SharedTask).filter(
        SharedTask.assigned_to == user_id
    ).order_by(SharedTask.created_at.desc()).all()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    group = db.query(Group).filter(Group.id == task_data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")

    assigned_user = db.query(User).filter(User.id == task_data.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="المستخدم المكلّف غير موجود")

    task = SharedTask(
        group_id=task_data.group_id,
        created_by=current_user_id,
        assigned_to=task_data.assigned_to,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    task = db.query(SharedTask).filter(SharedTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")

    if current_user_id not in {task.created_by, task.assigned_to}:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية تعديل هذه المهمة")

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task
