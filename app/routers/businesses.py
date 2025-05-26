# File: app/routers/businesses.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlmodel import Session, select
from datetime import datetime
from typing import List

from app.database.db import get_db
from app.models.business import Business
from app.models.user import User
from app.schemas import BusinessCreate, BusinessRead, BusinessUpdate
from app.services.auth import get_current_user
from app.core.codes import make_human_code
from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name
from openlocationcode import openlocationcode as olc
from app.schemas import BusinessCreate, BusinessRead, BusinessUpdate

router = APIRouter(
    prefix="/businesses",
    tags=["Businesses"],
)


@router.post(
    "/",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new business",
)
def create_business(
    payload: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessRead:
    digital_address = olc.encode(payload.latitude, payload.longitude)

    biz = Business(
        name=payload.name,
        short_description=payload.short_description,
        town_or_district=payload.town_or_district,
        contact_phone=payload.contact_phone,
        contact_email=payload.contact_email,
        contact_website=payload.contact_website,
        category=payload.category,
        region_code=payload.region_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        owner_id=current_user.id,
        average_rating=0.0,
        created_at=datetime.utcnow(),
        digital_address=digital_address,
    )
    db.add(biz)
    db.flush()  # so biz.id is populated

    # human-readable code
    house_no = make_human_code(
        current_user.country_code,
        payload.town_or_district[:3].lower(),
        biz.id
    )
    biz.house_no = house_no
    biz.code = house_no

    # postal lookup & reverse geocode
    postal = get_postal_service().nearest(
        payload.latitude, payload.longitude, current_user.country_code
    )
    road_name = get_road_name(payload.latitude, payload.longitude)

    biz.postal_code   = postal.postal_code
    biz.district_name = postal.place_name
    biz.road_name     = road_name
    biz.full_address  = (
        f"{road_name}, {house_no}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    db.commit()
    db.refresh(biz)
    return biz


@router.get(
    "/",
    response_model=List[BusinessRead],
    summary="List all businesses",
)
def list_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BusinessRead]:
    return db.exec(select(Business)).all()


@router.get(
    "/{business_id}",
    response_model=BusinessRead,
    summary="Get a business by ID",
)
def get_business(
    business_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessRead:
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    return biz


@router.patch(
    "/{business_id}",
    response_model=BusinessRead,
    summary="Update a business by ID",
)
def update_business(
    payload: BusinessUpdate,
    business_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BusinessRead:
    """
    Partially update fields of a business owned by the current user.
    """
    biz = db.get(Business, business_id)
    if not biz or biz.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Business not found or unauthorized")

    update_data = payload.dict(exclude_unset=True)
    for key, val in update_data.items():
        setattr(biz, key, val)

    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz

@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a business by ID",
)
def delete_business(
    business_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    biz = db.get(Business, business_id)
    if not biz or biz.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found or unauthorized"
        )
    db.delete(biz)
    db.commit()
