"""
مسارات المستخدمين والعلاقات الاجتماعية
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import (
    FollowRelation,
    FriendRequest,
    FriendRequestStatus,
    User,
    UserSettings,
)
from schemas import (
    FollowResponse,
    FriendRequestCreate,
    FriendRequestResponse,
    UserDetailResponse,
    UserResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
    UserUpdate,
)
from security import get_current_user as get_current_user_id

router = APIRouter(prefix="/api/users", tags=["Users"])


def _require_auth(current_user_id: str | None) -> str:
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يجب تسجيل الدخول"
        )
    return current_user_id


def _get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    return user


def _get_or_create_settings(db: Session, user_id: str) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _ensure_not_self(current_user_id: str, other_user_id: str, message: str):
    if current_user_id == other_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


def _add_friendship(user: User, friend: User):
    if friend not in user.friends:
        user.friends.append(friend)
    if user not in friend.friends:
        friend.friends.append(user)


def _remove_friendship(user: User, friend: User):
    if friend in user.friends:
        user.friends.remove(friend)
    if user in friend.friends:
        friend.friends.remove(user)


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    return _get_user_or_404(db, current_user_id)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    user = _get_user_or_404(db, current_user_id)

    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.get("/settings/me", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    return _get_or_create_settings(db, current_user_id)


@router.put("/settings/me", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    settings = _get_or_create_settings(db, current_user_id)

    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return db.query(User).offset(skip).limit(limit).all()


@router.post("/friends/{friend_id}")
async def add_friend(
    friend_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _ensure_not_self(current_user_id, friend_id, "لا يمكنك إضافة نفسك كصديق")

    user = _get_user_or_404(db, current_user_id)
    friend = _get_user_or_404(db, friend_id)
    _add_friendship(user, friend)
    db.commit()

    return {"success": True, "message": "تمت إضافة الصديق بنجاح"}


@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _ensure_not_self(current_user_id, friend_id, "لا يمكنك إزالة نفسك من الأصدقاء")

    user = _get_user_or_404(db, current_user_id)
    friend = _get_user_or_404(db, friend_id)
    _remove_friendship(user, friend)
    db.commit()

    return {"success": True, "message": "تمت إزالة الصديق بنجاح"}


@router.get("/{user_id}/friends", response_model=List[UserResponse])
async def get_user_friends(user_id: str, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    return user.friends


@router.post("/follow/{user_id}", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _ensure_not_self(current_user_id, user_id, "لا يمكنك متابعة نفسك")
    _get_user_or_404(db, user_id)

    relation = db.query(FollowRelation).filter(
        FollowRelation.follower_id == current_user_id,
        FollowRelation.following_id == user_id,
    ).first()

    if relation:
        return relation

    relation = FollowRelation(follower_id=current_user_id, following_id=user_id)
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    relation = db.query(FollowRelation).filter(
        FollowRelation.follower_id == current_user_id,
        FollowRelation.following_id == user_id,
    ).first()

    if relation:
        db.delete(relation)
        db.commit()

    return {"success": True, "message": "تم إلغاء المتابعة بنجاح"}


@router.get("/{user_id}/followers", response_model=List[UserResponse])
async def get_followers(user_id: str, db: Session = Depends(get_db)):
    _get_user_or_404(db, user_id)
    follower_ids = [
        row.follower_id
        for row in db.query(FollowRelation).filter(FollowRelation.following_id == user_id).all()
    ]
    if not follower_ids:
        return []
    return db.query(User).filter(User.id.in_(follower_ids)).all()


@router.get("/{user_id}/following", response_model=List[UserResponse])
async def get_following(user_id: str, db: Session = Depends(get_db)):
    _get_user_or_404(db, user_id)
    following_ids = [
        row.following_id
        for row in db.query(FollowRelation).filter(FollowRelation.follower_id == user_id).all()
    ]
    if not following_ids:
        return []
    return db.query(User).filter(User.id.in_(following_ids)).all()


@router.post("/friend-requests/{receiver_id}", response_model=FriendRequestResponse)
async def send_friend_request(
    receiver_id: str,
    payload: FriendRequestCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    _ensure_not_self(current_user_id, receiver_id, "لا يمكنك إرسال طلب صداقة لنفسك")

    sender = _get_user_or_404(db, current_user_id)
    receiver = _get_user_or_404(db, receiver_id)

    if receiver in sender.friends or sender in receiver.friends:
        raise HTTPException(status_code=400, detail="أنتم أصدقاء بالفعل")

    receiver_settings = _get_or_create_settings(db, receiver_id)
    if not receiver_settings.allow_friend_requests:
        raise HTTPException(status_code=403, detail="هذا المستخدم لا يستقبل طلبات صداقة حالياً")

    existing = db.query(FriendRequest).filter(
        or_(
            (FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == receiver_id),
            (FriendRequest.sender_id == receiver_id) & (FriendRequest.receiver_id == current_user_id),
        )
    ).first()

    if existing:
        if existing.status == FriendRequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="يوجد طلب صداقة معلّق بالفعل")
        existing.sender_id = current_user_id
        existing.receiver_id = receiver_id
        existing.message = payload.message
        existing.status = FriendRequestStatus.PENDING
        existing.responded_at = None
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    request_item = FriendRequest(
        sender_id=current_user_id,
        receiver_id=receiver_id,
        message=payload.message,
        status=FriendRequestStatus.PENDING,
    )
    db.add(request_item)
    db.commit()
    db.refresh(request_item)
    return request_item


@router.get("/friend-requests/incoming", response_model=List[FriendRequestResponse])
async def get_incoming_friend_requests(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    return db.query(FriendRequest).filter(
        FriendRequest.receiver_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).order_by(FriendRequest.created_at.desc()).all()


@router.get("/friend-requests/outgoing", response_model=List[FriendRequestResponse])
async def get_outgoing_friend_requests(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    return db.query(FriendRequest).filter(
        FriendRequest.sender_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.PENDING,
    ).order_by(FriendRequest.created_at.desc()).all()


@router.post("/friend-requests/{request_id}/accept", response_model=FriendRequestResponse)
async def accept_friend_request(
    request_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    request_item = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not request_item:
        raise HTTPException(status_code=404, detail="طلب الصداقة غير موجود")
    if request_item.receiver_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية قبول هذا الطلب")
    if request_item.status != FriendRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="تمت معالجة هذا الطلب من قبل")

    sender = _get_user_or_404(db, request_item.sender_id)
    receiver = _get_user_or_404(db, request_item.receiver_id)
    _add_friendship(sender, receiver)

    request_item.status = FriendRequestStatus.ACCEPTED
    request_item.responded_at = datetime.utcnow()
    request_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request_item)
    return request_item


@router.post("/friend-requests/{request_id}/reject", response_model=FriendRequestResponse)
async def reject_friend_request(
    request_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    request_item = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not request_item:
        raise HTTPException(status_code=404, detail="طلب الصداقة غير موجود")
    if request_item.receiver_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية رفض هذا الطلب")
    if request_item.status != FriendRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="تمت معالجة هذا الطلب من قبل")

    request_item.status = FriendRequestStatus.REJECTED
    request_item.responded_at = datetime.utcnow()
    request_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request_item)
    return request_item


@router.delete("/friend-requests/{request_id}")
async def cancel_friend_request(
    request_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    request_item = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not request_item:
        raise HTTPException(status_code=404, detail="طلب الصداقة غير موجود")
    if current_user_id not in {request_item.sender_id, request_item.receiver_id}:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية إلغاء هذا الطلب")
    if request_item.status != FriendRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="لا يمكن إلغاء طلب تمّت معالجته")

    request_item.status = FriendRequestStatus.CANCELLED
    request_item.responded_at = datetime.utcnow()
    request_item.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "تم إلغاء طلب الصداقة"}


@router.post("/ban/{user_id}")
async def ban_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    admin = _get_user_or_404(db, current_user_id)
    if admin.role.value != "admin":
        raise HTTPException(status_code=403, detail="ليس لديك صلاحيات كافية")

    user = _get_user_or_404(db, user_id)
    user.is_banned = True
    db.commit()
    return {"success": True, "message": "تم حظر المستخدم بنجاح"}


@router.post("/unban/{user_id}")
async def unban_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    current_user_id = _require_auth(current_user_id)
    admin = _get_user_or_404(db, current_user_id)
    if admin.role.value != "admin":
        raise HTTPException(status_code=403, detail="ليس لديك صلاحيات كافية")

    user = _get_user_or_404(db, user_id)
    user.is_banned = False
    db.commit()
    return {"success": True, "message": "تم إلغاء حظر المستخدم بنجاح"}


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    return _get_user_or_404(db, user_id)
