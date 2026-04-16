"""
مسارات السوق
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import MarketplaceItem, MarketplaceItemStatus, User
from schemas import MarketplaceItemCreate, MarketplaceItemUpdate, MarketplaceItemResponse
from security import get_current_user

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])


@router.get("", response_model=List[MarketplaceItemResponse])
async def list_marketplace_items(
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(MarketplaceItem)

    if category:
        query = query.filter(MarketplaceItem.category == category)
    if status_filter:
        query = query.filter(MarketplaceItem.status == status_filter)

    return query.order_by(MarketplaceItem.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=MarketplaceItemResponse)
async def get_marketplace_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    return item


@router.post("", response_model=MarketplaceItemResponse, status_code=status.HTTP_201_CREATED)
async def create_marketplace_item(
    data: MarketplaceItemCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    item = MarketplaceItem(
        seller_id=current_user_id,
        group_id=data.group_id,
        title=data.title,
        description=data.description,
        price=data.price,
        currency=data.currency,
        category=data.category,
        location=data.location,
        image_urls=data.image_urls,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MarketplaceItemResponse)
async def update_marketplace_item(
    item_id: str,
    data: MarketplaceItemUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    if item.seller_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية تعديل هذا العنصر")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}/status/{item_status}", response_model=MarketplaceItemResponse)
async def update_marketplace_item_status(
    item_id: str,
    item_status: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    if not current_user_id:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول")

    item = db.query(MarketplaceItem).filter(MarketplaceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    if item.seller_id != current_user_id:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية تعديل هذا العنصر")

    try:
        item.status = MarketplaceItemStatus(item_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="حالة العنصر غير صحيحة") from exc

    db.commit()
    db.refresh(item)
    return item
