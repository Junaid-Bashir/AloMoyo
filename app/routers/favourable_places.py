# app/routers/favourable_places.py

from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.favourable_place import FavourablePlace
from app.schemas import FavourablePlaceCreate, FavourablePlaceRead, MeModel
from app.routers.auth import get_current_user
from app.core.codes import make_human_code

from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name   # ← Add this import

from openlocationcode import openlocationcode as olc

router = APIRouter(prefix="/favourable_places", tags=["FavourablePlaces"])

@router.post("/", response_model=FavourablePlaceRead)
def create_favourable_place(
    payload: FavourablePlaceCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> FavourablePlaceRead:
    # 1) Plus Code
    digital_address = olc.encode(payload.latitude, payload.longitude)

    # 2) Save to DB
    place = FavourablePlace(
        **payload.dict(),
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        digital_address=digital_address,
    )
    db.add(place)
    db.commit()
    db.refresh(place)

    # 3) Human Code
    place.code = make_human_code(
        current_user.country_code,
        payload.label[:3].lower(),
        place.id,
    )

    # 4) Postal lookup
    ps = get_postal_service()
    postal = ps.nearest(
        payload.latitude,
        payload.longitude,
        current_user.country_code,
    )

    # 5) Road name
    road_name = get_road_name(payload.latitude, payload.longitude)

    # 6) Full address
    full_address = (
        f"{road_name}, {place.code}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    place.postal_code = postal.postal_code
    place.district_name = postal.place_name
    place.full_address = full_address

    db.add(place)
    db.commit()
    db.refresh(place)

    return place

@router.get("/", response_model=List[FavourablePlaceRead])
def list_favourable_places(db: Session = Depends(get_db)) -> List[FavourablePlaceRead]:
    return db.exec(select(FavourablePlace)).all()
