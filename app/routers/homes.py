# app/routers/homes.py

from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.home import Home
from app.schemas import HomeCreate, HomeRead, MeModel
from app.routers.auth import get_current_user
from app.core.codes import make_human_code

from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name   # ← Add this import

from openlocationcode import openlocationcode as olc

router = APIRouter(prefix="/homes", tags=["Homes"])

@router.post("/", response_model=HomeRead)
def create_home(
    payload: HomeCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> HomeRead:
    # 1) Plus Code
    digital_address = olc.encode(payload.latitude, payload.longitude)

    # 2) Save to DB to get ID
    home = Home(
        **payload.dict(),
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        digital_address=digital_address,
    )
    db.add(home)
    db.commit()
    db.refresh(home)

    # 3) Human Code
    home.code = make_human_code(
        current_user.country_code,
        payload.title[:3].lower(),
        home.id,
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
        f"{road_name}, {home.code}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    home.postal_code = postal.postal_code
    home.district_name = postal.place_name
    home.full_address = full_address

    db.add(home)
    db.commit()
    db.refresh(home)

    return home

@router.get("/", response_model=List[HomeRead])
def list_homes(db: Session = Depends(get_db)) -> List[HomeRead]:
    return db.exec(select(Home)).all()
