# app/routers/contributions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.contribution import Contribution
from app.schemas import ContributionCreate, ContributionRead, MeModel
from app.routers.auth import get_current_user, get_current_admin

from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name

from openlocationcode import openlocationcode as olc
from app.core.codes import make_human_code

router = APIRouter(prefix="/contributions", tags=["Contributions"])

def extract_lat_lon_from_wkt(wkt: str) -> tuple:
    try:
        if wkt.startswith("POINT"):
            coords = wkt.replace("POINT(", "").replace(")", "").split()
            lon, lat = map(float, coords)
            return lat, lon
    except Exception:
        pass
    return None, None

@router.post("/", response_model=ContributionRead)
def submit_contribution(
    payload: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> ContributionRead:
    contrib = Contribution(
        **payload.dict(),
        submitted_by_user_id=current_user.id,
        created_at=datetime.utcnow(),
        is_approved=False,
    )
    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    return contrib

@router.patch("/{contrib_id}/approve", response_model=ContributionRead)
def approve_contribution(
    contrib_id: int,
    db: Session = Depends(get_db),
    admin: MeModel = Depends(get_current_admin),
) -> ContributionRead:
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(404, "Not found")

    contrib.is_approved = True

    if contrib.wkt:
        lat, lon = extract_lat_lon_from_wkt(contrib.wkt)
        if lat is None or lon is None:
            raise HTTPException(400, "Could not extract coordinates from WKT")

        # 1) plus code
        contrib.digital_address = olc.encode(lat, lon)
        # 2) human code
        human_code = make_human_code(admin.country_code, "ctb", contrib.id)
        contrib.code = human_code

        # 3) postal lookup
        ps = get_postal_service()
        postal = ps.nearest(lat, lon, admin.country_code)

        # 4) road name
        road_name = get_road_name(lat, lon)

        # 5) full address
        contrib.postal_code = postal.postal_code
        contrib.district_name = postal.place_name
        contrib.full_address = (
            f"{road_name}, {human_code}, "
            f"{postal.postal_code}, {postal.place_name}, "
            f"{admin.country_code.upper()}"
        )

    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    return contrib

@router.get("/", response_model=List[ContributionRead])
def list_contributions(
    db: Session = Depends(get_db),
) -> List[ContributionRead]:
    return db.exec(select(Contribution)).all()
