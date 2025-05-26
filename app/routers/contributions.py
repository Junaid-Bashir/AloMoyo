# File: app/routers/contributions.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlmodel import Session, select
from typing import List

from shapely import wkt as shapely_wkt

from app.database.db import get_db
from app.models.contribution import Contribution
from app.schemas import ContributionCreate, ContributionRead, ContributionUpdate
from app.services.auth import get_current_user, get_current_admin
from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name

router = APIRouter(
    prefix="/contributions",
    tags=["Contributions"],
)


def extract_latlon_from_wkt(wkt_str: str) -> tuple[float, float]:
    """
    Parse a WKT POINT string into (lat, lon).
    Expects 'POINT(lon lat)'.
    """
    geom = shapely_wkt.loads(wkt_str)
    return geom.y, geom.x


@router.post(
    "/",
    response_model=ContributionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new contribution"
)
def create_contribution(
    payload: ContributionCreate = Body(...),
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


@router.get(
    "/",
    response_model=List[ContributionRead],
    summary="List all contributions"
)
def list_contributions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[ContributionRead]:
    """
    Returns all contributions.  (Could filter by user or approval status if desired.)
    """
    return db.exec(select(Contribution)).all()


@router.get(
    "/{contrib_id}",
    response_model=ContributionRead,
    summary="Get a single contribution by ID"
)
def read_contribution(
    contrib_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ContributionRead:
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contrib


@router.patch(
    "/{contrib_id}",
    response_model=ContributionRead,
    summary="Update your contribution (before approval)"
)
def update_contribution(
    payload: ContributionUpdate = Body(...),
    contrib_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ContributionRead:
    """
    Allows the original submitter to modify the WKT before it's approved.
    """
    contrib = db.get(Contribution, contrib_id)
    if not contrib or contrib.submitted_by_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Not found or unauthorized")

    updates = payload.dict(exclude_unset=True)
    if "wkt" in updates:
        contrib.wkt = updates["wkt"]
        # re‐compute address fields
        lat, lon = extract_latlon_from_wkt(contrib.wkt)
        postal = get_postal_service().nearest(lat, lon, current_user.country_code)
        road_name = get_road_name(lat, lon)
        contrib.postal_code   = postal.postal_code
        contrib.district_name = postal.place_name
        contrib.road_name     = road_name
        contrib.full_address  = (
            f"{road_name}, {postal.postal_code}, "
            f"{postal.place_name}, {current_user.country_code.upper()}"
        )

    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    return contrib


@router.delete(
    "/{contrib_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contribution"
)
def delete_contribution(
    contrib_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    """
    Delete your own contribution, or allow admins to delete any.
    """
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")

    # allow owner or admin
    if contrib.submitted_by_user_id != current_user.id:
        # second Depends to check admin
        _ = get_current_admin(current_user)
    db.delete(contrib)
    db.commit()


@router.post(
    "/{contrib_id}/approve",
    response_model=ContributionRead,
    summary="Approve a contribution (admin only)"
)
def approve_contribution(
    contrib_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> ContributionRead:
    """
    Mark a contribution as approved.  Admins only.
    """
    contrib = db.get(Contribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribution not found")
    contrib.is_approved = True
    db.add(contrib)
    db.commit()
    db.refresh(contrib)
    return contrib
