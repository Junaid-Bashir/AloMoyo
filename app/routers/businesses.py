# File: app/routers/businesses.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional

from app.database.db     import get_db
from app.models.business import Business
from app.schemas         import BusinessCreate, BusinessRead, MeModel
from app.routers.auth    import get_current_user
from app.core.codes      import make_human_code
from app.services.postal_service import get_postal_service
from app.services.geocode        import get_road_name
from openlocationcode            import openlocationcode as olc

router = APIRouter(prefix="/businesses", tags=["Businesses"])

@router.post("/", response_model=BusinessRead, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> BusinessRead:
    # 1) Generate plus code
    digital_address = olc.encode(payload.latitude, payload.longitude)

    # 2) Build initial Business (only non-nullable fields)
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

    # 3) Add to session and flush to get biz.id
    db.add(biz)
    db.flush()

    # 4) Generate the human code now that biz.id exists (used as house number)
    house_no = make_human_code(
        current_user.country_code,
        payload.town_or_district[:3].lower(),
        biz.id
    )
    biz.house_no = house_no

    # 5) Also store it in the code field so the response validation passes
    biz.code = house_no

    # 6) Lookup nearest postal info (with Uganda override)
    postal = get_postal_service().nearest(
        payload.latitude, payload.longitude, current_user.country_code
    )

    # 7) Reverse‐geocode road name
    road_name = get_road_name(payload.latitude, payload.longitude)

    # 8) Populate remaining address fields
    biz.postal_code   = postal.postal_code
    biz.district_name = postal.place_name
    biz.road_name     = road_name
    biz.full_address  = (
        f"{road_name}, {house_no}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    # 9) Commit once with all fields set
    db.commit()
    db.refresh(biz)

    return biz

@router.get("/", response_model=List[BusinessRead])
def list_businesses(db: Session = Depends(get_db)) -> List[BusinessRead]:
    return db.exec(select(Business)).all()
