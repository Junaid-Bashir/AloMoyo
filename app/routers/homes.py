# File: app/routers/homes.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.home import Home
from app.schemas import HomeCreate, HomeRead, HomeUpdate, MeModel
from app.services.auth import get_current_user
from app.core.codes import make_human_code
from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name
from openlocationcode import openlocationcode as olc

router = APIRouter(
    prefix="/homes",
    tags=["Homes"],
    dependencies=[Depends(get_current_user)],  # secure all routes here
)


@router.post(
    "/",
    response_model=HomeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new home/work location"
)
def create_home(
    payload: HomeCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> HomeRead:
    # 1) Generate Plus Code
    digital_address = olc.encode(payload.latitude, payload.longitude)

    # 2) Persist initial record
    home = Home(
        **payload.dict(),
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        digital_address=digital_address,
    )
    db.add(home)
    db.commit()
    db.refresh(home)

    # 3) Human‐readable code
    home.code = make_human_code(
        current_user.country_code,
        payload.title[:3].lower(),
        home.id,
    )

    # 4) Postal lookup
    postal = get_postal_service().nearest(
        payload.latitude,
        payload.longitude,
        current_user.country_code,
    )

    # 5) Reverse‐geocode street name
    road_name = get_road_name(payload.latitude, payload.longitude)

    # 6) Build & persist full address
    home.postal_code   = postal.postal_code
    home.district_name = postal.place_name
    home.road_name     = road_name
    home.full_address  = (
        f"{road_name}, {home.code}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    db.add(home)
    db.commit()
    db.refresh(home)

    return home


@router.get(
    "/",
    response_model=List[HomeRead],
    summary="List all your saved home/work locations"
)
def list_homes(
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> List[HomeRead]:
    """
    Returns only the homes belonging to the current user.
    """
    stmt = select(Home).where(Home.owner_id == current_user.id)
    return db.exec(stmt).all()


@router.get(
    "/{home_id}",
    response_model=HomeRead,
    summary="Get a home/work location by ID"
)
def get_home(
    home_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> HomeRead:
    """
    Retrieve a specific home/work location by its ID.
    """
    home = db.get(Home, home_id)
    if not home or home.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home not found or unauthorized"
        )
    return home


@router.patch(
    "/{home_id}",
    response_model=HomeRead,
    summary="Update a home/work location by ID"
)
def update_home(
    payload: HomeUpdate = Body(...),
    home_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> HomeRead:
    """
    Partially update a home/work location owned by the current user.
    """
    home = db.get(Home, home_id)
    if not home or home.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home not found or unauthorized"
        )

    updates = payload.dict(exclude_unset=True)
    for key, val in updates.items():
        setattr(home, key, val)

    # (Optionally re-run plus-code/postal/road logic if coords changed)

    db.add(home)
    db.commit()
    db.refresh(home)
    return home


@router.delete(
    "/{home_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a home/work location by ID"
)
def delete_home(
    home_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
):
    """
    Delete a home/work location owned by the current user.
    """
    home = db.get(Home, home_id)
    if not home or home.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home not found or unauthorized"
        )
    db.delete(home)
    db.commit()
