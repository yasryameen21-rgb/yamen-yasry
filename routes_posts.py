"""
مسارات المنشورات والتفاعلات والحفظ وإعادة النشر
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Comment, Post, PostShare, SavedPost, User
from schemas import (
    CommentCreate,
    CommentResponse,
    PostCreate,
    PostResponse,
    PostStatsResponse,
    PostUpdate,
    RepostCreate,
)
from security import get_current_user as get_current_user_id

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def _require_auth(current_user_id: str | None) -> str:
    if not current_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="يجب تسجيل الدخول")
    return current_user_id


def _get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return user


def _get_post_or_404(db: Session, post_id: str) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="المنشور غير موجود")
    return post


def _reaction_breakdown(post: Post) -> dict[str, int]:
    reactions = post.reactions or {}
    return {
        reaction_type: len(user_ids)
        for reaction_type, user_ids in reactions.items()
        if isinstance(user_ids, list)
    }


@router.post("", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    user = _get_user_or_404(db, current_user_id)

    if user.is_muted_from_posting:
        raise HTTPException(status_code=403, detail="تم منع هذا الحساب من النشر")

    new_post = Post(
        user_id=current_user_id,
        group_id=post_data.group_id,
        content=post_data.content,
        post_type=post_data.post_type,
        media_url=post_data.media_url,
        link_preview_url=post_data.link_preview_url,
        link_preview_title=post_data.link_preview_title,
        link_preview_description=post_data.link_preview_description,
        link_preview_image=post_data.link_preview_image,
        reactions={},
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("", response_model=List[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    group_id: Optional[str] = None,
    user_id: Optional[str] = None,
    post_type: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Post).filter(Post.is_hidden == False)

    if group_id:
        query = query.filter(Post.group_id == group_id)
    if user_id:
        query = query.filter(Post.user_id == user_id)
    if post_type:
        query = query.filter(Post.post_type == post_type)
    if q:
        query = query.filter(Post.content.ilike(f"%{q}%"))

    return query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/saved/me", response_model=List[PostResponse])
async def get_saved_posts(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    saved = db.query(SavedPost).filter(SavedPost.user_id == current_user_id).order_by(SavedPost.created_at.desc()).all()
    if not saved:
        return []
    posts = []
    for item in saved:
        post = db.query(Post).filter(Post.id == item.post_id, Post.is_hidden == False).first()
        if post:
            posts.append(post)
    return posts


@router.get("/{post_id}/stats", response_model=PostStatsResponse)
async def get_post_stats(post_id: str, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    reactions_breakdown = _reaction_breakdown(post)
    return {
        "post_id": post.id,
        "likes_count": reactions_breakdown.get("like", 0),
        "comments_count": db.query(Comment).filter(Comment.post_id == post.id).count(),
        "shares_count": post.shares_count or 0,
        "saves_count": db.query(SavedPost).filter(SavedPost.post_id == post.id).count(),
        "reactions_breakdown": reactions_breakdown,
    }


@router.post("/{post_id}/save")
async def save_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _get_post_or_404(db, post_id)

    existing = db.query(SavedPost).filter(
        SavedPost.user_id == current_user_id,
        SavedPost.post_id == post_id,
    ).first()
    if existing:
        return {"success": True, "message": "المنشور محفوظ بالفعل"}

    saved_post = SavedPost(user_id=current_user_id, post_id=post_id)
    db.add(saved_post)
    db.commit()
    return {"success": True, "message": "تم حفظ المنشور"}


@router.delete("/{post_id}/save")
async def unsave_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    existing = db.query(SavedPost).filter(
        SavedPost.user_id == current_user_id,
        SavedPost.post_id == post_id,
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"success": True, "message": "تم إلغاء حفظ المنشور"}


@router.post("/{post_id}/repost", response_model=PostResponse)
async def repost_post(
    post_id: str,
    payload: RepostCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    original_post = _get_post_or_404(db, post_id)

    prefix = payload.content.strip() if payload.content else ""
    repost_content = f"إعادة نشر من {original_post.user_id}:\n{original_post.content}"
    if prefix:
        repost_content = f"{prefix}\n\n{repost_content}"

    new_post = Post(
        user_id=current_user_id,
        group_id=original_post.group_id,
        content=repost_content,
        post_type=original_post.post_type,
        media_url=original_post.media_url,
        link_preview_url=original_post.link_preview_url,
        link_preview_title=original_post.link_preview_title,
        link_preview_description=original_post.link_preview_description,
        link_preview_image=original_post.link_preview_image,
        reactions={},
    )
    db.add(new_post)
    db.flush()

    original_post.shares_count = (original_post.shares_count or 0) + 1
    db.add(PostShare(user_id=current_user_id, original_post_id=original_post.id, repost_post_id=new_post.id))
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, db: Session = Depends(get_db)):
    post = _get_post_or_404(db, post_id)
    if post.is_hidden:
        raise HTTPException(status_code=403, detail="هذا المنشور مخفي")
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    post = _get_post_or_404(db, post_id)

    if post.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا يمكنك تحديث منشور شخص آخر")

    update_data = post_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    post = _get_post_or_404(db, post_id)

    if post.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا يمكنك حذف منشور شخص آخر")

    db.query(SavedPost).filter(SavedPost.post_id == post_id).delete()
    db.query(PostShare).filter(
        (PostShare.original_post_id == post_id) | (PostShare.repost_post_id == post_id)
    ).delete()
    db.delete(post)
    db.commit()
    return {"success": True, "message": "تم حذف المنشور بنجاح"}


@router.post("/{post_id}/reactions/{reaction_type}")
async def add_reaction(
    post_id: str,
    reaction_type: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    post = _get_post_or_404(db, post_id)

    reactions = post.reactions or {}
    if reaction_type not in reactions:
        reactions[reaction_type] = []

    if current_user_id not in reactions[reaction_type]:
        reactions[reaction_type].append(current_user_id)

    post.reactions = reactions
    db.commit()
    return {"success": True, "message": "تم إضافة التفاعل بنجاح"}


@router.delete("/{post_id}/reactions/{reaction_type}")
async def remove_reaction(
    post_id: str,
    reaction_type: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    post = _get_post_or_404(db, post_id)

    reactions = post.reactions or {}
    if reaction_type in reactions and current_user_id in reactions[reaction_type]:
        reactions[reaction_type].remove(current_user_id)
        if not reactions[reaction_type]:
            reactions.pop(reaction_type, None)

    post.reactions = reactions
    db.commit()
    return {"success": True, "message": "تم إزالة التفاعل بنجاح"}


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _get_post_or_404(db, post_id)
    user = _get_user_or_404(db, current_user_id)

    if user.is_muted_from_commenting:
        raise HTTPException(status_code=403, detail="تم منع هذا الحساب من التعليق")

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user_id,
        content=comment_data.content,
        reactions={},
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    _get_post_or_404(db, post_id)
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")
    if comment.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا يمكنك حذف تعليق شخص آخر")

    db.delete(comment)
    db.commit()
    return {"success": True, "message": "تم حذف التعليق بنجاح"}


@router.post("/comments/{comment_id}/reactions/{reaction_type}")
async def add_comment_reaction(
    comment_id: str,
    reaction_type: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="التعليق غير موجود")

    reactions = comment.reactions or {}
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    if current_user_id not in reactions[reaction_type]:
        reactions[reaction_type].append(current_user_id)

    comment.reactions = reactions
    db.commit()
    return {"success": True, "message": "تم إضافة التفاعل بنجاح"}
