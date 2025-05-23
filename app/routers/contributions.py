# app/routers/contributions.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select
from typing import List

from shapely import wkt as shapely_wkt

from app.database.db import get_db
from app.models.contribution import Contribution
from app.schemas import ContributionCreate, ContributionRead
from app.services.auth import get_current_user, get_current_admin
from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name

router = APIRouter(prefix="/contributions", tags=["Contributions"])


def extract_latlon_from_wkt(wkt_str: str) -> tuple[float, float]:
    """
    Parse a WKT POINT string into (lat, lon).
    Expects 'POINT(lon lat)'.
    """
    geom = shapely_wkt.loads(wkt_str)
    return geom.y, geom.x


@router.post("/", response_model=ContributionRead, status_code=status.HTTP_201_CREATED)
def create_contribution(
    payload: ContributionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ContributionRead:
    # 1) Store the raw WKT
    contrib = Contribution(
        wkt=payload.wkt,
        submitted_by_user_id=current_user.id,
        is_approved=False,
    )
    db.add(contrib)
    db.flush()

    # 2) Extract lat/lon and enrich
    lat, lon = extract_latlon_from_wkt(payload.wkt)
    postal = get_postal_service().nearest(lat, lon, current_user.country_code)
    road_name = get_road_name(lat, lon)

    # 3) Fill in address fields
    contrib.postal_code   = postal.postal_code
    contrib.district_name = postal.place_name
    contrib.road_name     = road_name
    contrib.full_address  = (
        f"{road_name}, {postal.postal_code}, "
        f"{postal.place_name}, {current_user.country_code.upper()}"
    )

    db.commit()
    db.refresh(contrib)
    return contrib


@router.get("/", response_model=List[ContributionRead])
def list_contributions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[ContributionRead]:
    return db.exec(select(Contribution)).all()


@router.get("/{contrib_id}", response_model=ContributionRead)
def read_contribution(
    contrib_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ContributionRead:
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contrib


@router.post("/{contrib_id}/approve", response_model=ContributionRead)
def approve_contribution(
    contrib_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin),
) -> ContributionRead:
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    contrib.is_approved = True
    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    return contrib
