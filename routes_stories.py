"""
مسارات القصص
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Story
from schemas import StoryCreate, StoryResponse
from security import get_current_user

router = APIRouter(prefix="/api/stories", tags=["Stories"])


@router.get("", response_model=List[StoryResponse])
async def list_stories(
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Story).filter(Story.expires_at > datetime.utcnow())
    if user_id:
        query = query.filter(Story.user_id == user_id)
    return query.order_by(Story.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    data: StoryCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    story = Story(
        user_id=current_user_id,
        media_url=data.media_url,
        media_type=data.media_type,
        expires_at=datetime.utcnow() + timedelta(hours=24),
        viewed_by_users=[],
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


@router.put("/{story_id}/view")
async def mark_story_viewed(
    story_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="القصة غير موجودة")

    viewed_by_users = story.viewed_by_users or []
    if current_user_id not in viewed_by_users:
        viewed_by_users.append(current_user_id)
        story.viewed_by_users = viewed_by_users
        db.commit()

    return {"success": True, "message": "تم تسجيل المشاهدة"}
