"""
مسارات مستقلة للتعليقات لتثبيت العقد بين الـ API والعملاء.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Comment, Post, User
from schemas import CommentResponse, CommentUpdate
from security import get_current_user as get_current_user_id

router = APIRouter(prefix="/api/comments", tags=["Comments"])


def _require_auth(current_user_id: str | None) -> str:
    if not current_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="يجب تسجيل الدخول")
    return current_user_id


def _get_comment_or_404(db: Session, comment_id: str) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")
    return comment


@router.get("", response_model=List[CommentResponse])
async def list_comments(
    post_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Comment)

    if post_id:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="المنشور غير موجود")
        query = query.filter(Comment.post_id == post_id)

    return query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: str, db: Session = Depends(get_db)):
    return _get_comment_or_404(db, comment_id)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user_id = _require_auth(current_user_id)
    comment = _get_comment_or_404(db, comment_id)

    if comment.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا يمكنك تحديث تعليق شخص آخر")

    update_data = comment_data.dict(exclude_unset=True)
    if not update_data:
        return comment

    for field, value in update_data.items():
        setattr(comment, field, value)

    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user_id = _require_auth(current_user_id)
    comment = _get_comment_or_404(db, comment_id)

    if comment.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا يمكنك حذف تعليق شخص آخر")

    db.delete(comment)
    db.commit()
    return {"success": True, "message": "تم حذف التعليق بنجاح"}


@router.post("/{comment_id}/reactions/{reaction_type}")
async def add_comment_reaction(
    comment_id: str,
    reaction_type: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user_id = _require_auth(current_user_id)
    comment = _get_comment_or_404(db, comment_id)

    reactions = comment.reactions or {}
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    if current_user_id not in reactions[reaction_type]:
        reactions[reaction_type].append(current_user_id)

    comment.reactions = reactions
    db.commit()
    return {"success": True, "message": "تم إضافة التفاعل بنجاح"}


@router.delete("/{comment_id}/reactions/{reaction_type}")
async def remove_comment_reaction(
    comment_id: str,
    reaction_type: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    current_user_id = _require_auth(current_user_id)
    comment = _get_comment_or_404(db, comment_id)

    reactions = comment.reactions or {}
    if reaction_type in reactions and current_user_id in reactions[reaction_type]:
        reactions[reaction_type].remove(current_user_id)
        if not reactions[reaction_type]:
            reactions.pop(reaction_type, None)

    comment.reactions = reactions
    db.commit()
    return {"success": True, "message": "تمت إزالة التفاعل بنجاح"}
