"""
مسارات المنشورات
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from database import get_db
from models import Post, Comment, User, ReactionType
from schemas import PostCreate, PostResponse, PostUpdate, CommentCreate, CommentResponse

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.post("", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إنشاء منشور جديد
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    if user.is_muted_from_posting:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تم منع هذا الحساب من النشر"
        )
    
    # إنشاء المنشور
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
        reactions={}
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, db: Session = Depends(get_db)):
    """
    الحصول على منشور معين
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    if post.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا المنشور مخفي"
        )
    
    return post


@router.get("", response_model=List[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    group_id: str = None,
    db: Session = Depends(get_db)
):
    """
    الحصول على قائمة المنشورات
    """
    query = db.query(Post).filter(Post.is_hidden == False)
    
    if group_id:
        query = query.filter(Post.group_id == group_id)
    
    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    تحديث منشور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    if post.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك تحديث منشور شخص آخر"
        )
    
    # تحديث البيانات
    update_data = post_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    
    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    حذف منشور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    if post.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك حذف منشور شخص آخر"
        )
    
    db.delete(post)
    db.commit()
    
    return {"success": True, "message": "تم حذف المنشور بنجاح"}


# ==================== مسارات التفاعلات ====================

@router.post("/{post_id}/reactions/{reaction_type}")
async def add_reaction(
    post_id: str,
    reaction_type: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إضافة تفاعل على منشور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    # تحديث التفاعلات
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
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إزالة تفاعل من منشور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    # تحديث التفاعلات
    reactions = post.reactions or {}
    if reaction_type in reactions and current_user_id in reactions[reaction_type]:
        reactions[reaction_type].remove(current_user_id)
    
    post.reactions = reactions
    db.commit()
    
    return {"success": True, "message": "تم إزالة التفاعل بنجاح"}


# ==================== مسارات التعليقات ====================

@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إضافة تعليق على منشور
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المنشور غير موجود"
        )
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if user.is_muted_from_commenting:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تم منع هذا الحساب من التعليق"
        )
    
    # إنشاء التعليق
    new_comment = Comment(
        post_id=post_id,
        user_id=current_user_id,
        content=comment_data.content,
        reactions={}
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
    """
    الحصول على تعليقات منشور
    """
    comments = db.query(Comment).filter(
        Comment.post_id == post_id
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    حذف تعليق
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التعليق غير موجود"
        )
    
    if comment.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك حذف تعليق شخص آخر"
        )
    
    db.delete(comment)
    db.commit()
    
    return {"success": True, "message": "تم حذف التعليق بنجاح"}


@router.post("/comments/{comment_id}/reactions/{reaction_type}")
async def add_comment_reaction(
    comment_id: str,
    reaction_type: str,
    current_user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    إضافة تفاعل على تعليق
    """
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التعليق غير موجود"
        )
    
    # تحديث التفاعلات
    reactions = comment.reactions or {}
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    
    if current_user_id not in reactions[reaction_type]:
        reactions[reaction_type].append(current_user_id)
    
    comment.reactions = reactions
    db.commit()
    
    return {"success": True, "message": "تم إضافة التفاعل بنجاح"}
