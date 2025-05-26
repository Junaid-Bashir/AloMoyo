# File: app/routers/favourable_places.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.favourable_place import FavourablePlace
from app.schemas import (
    FavourablePlaceCreate,
    FavourablePlaceRead,
    FavourablePlaceUpdate,
    MeModel,
)
from app.services.auth import get_current_user
from app.core.codes import make_human_code
from app.services.postal_service import get_postal_service
from app.services.geocode import get_road_name
from openlocationcode import openlocationcode as olc

router = APIRouter(
    prefix="/favourable_places",
    tags=["FavourablePlaces"],
    dependencies=[Depends(get_current_user)],  # secure all routes
)


@router.post(
    "/",
    response_model=FavourablePlaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new POI"
)
def create_favourable_place(
    payload: FavourablePlaceCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> FavourablePlaceRead:
    # 1) Plus Code
    digital_address = olc.encode(payload.latitude, payload.longitude)

    # 2) Persist initial record
    place = FavourablePlace(
        **payload.dict(),
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        digital_address=digital_address,
    )
    db.add(place)
    db.commit()
    db.refresh(place)

    # 3) Human‐readable code
    place.code = make_human_code(
        current_user.country_code,
        payload.label[:3].lower(),
        place.id,
    )

    # 4) Postal lookup
    postal = get_postal_service().nearest(
        payload.latitude, payload.longitude, current_user.country_code
    )

    # 5) Reverse‐geocode street name
    road_name = get_road_name(payload.latitude, payload.longitude)

    # 6) Build & persist full address
    place.postal_code   = postal.postal_code
    place.district_name = postal.place_name
    place.road_name     = road_name
    place.full_address  = (
        f"{road_name}, {place.code}, "
        f"{postal.postal_code}, {postal.place_name}, "
        f"{current_user.country_code.upper()}"
    )

    db.add(place)
    db.commit()
    db.refresh(place)

    return place


@router.get(
    "/",
    response_model=List[FavourablePlaceRead],
    summary="List all POIs"
)
def list_favourable_places(
    db: Session = Depends(get_db),
) -> List[FavourablePlaceRead]:
    """
    Returns all points of interest accessible to the current user.
    """
    return db.exec(select(FavourablePlace)).all()


@router.get(
    "/{place_id}",
    response_model=FavourablePlaceRead,
    summary="Get a single POI by ID"
)
def get_favourable_place(
    place_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
) -> FavourablePlaceRead:
    """
    Retrieve a specific point of interest by its ID.
    """
    place = db.get(FavourablePlace, place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favourable place not found"
        )
    return place


@router.patch(
    "/{place_id}",
    response_model=FavourablePlaceRead,
    summary="Update a POI by ID"
)
def update_favourable_place(
    payload: FavourablePlaceUpdate = Body(...),
    place_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> FavourablePlaceRead:
    """
    Partially update a POI owned by the current user.
    """
    place = db.get(FavourablePlace, place_id)
    if not place or place.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POI not found or unauthorized"
        )

    updates = payload.dict(exclude_unset=True)
    for key, val in updates.items():
        setattr(place, key, val)

    # if coords changed, you might re-run plus‐code, postal, road logic here...

    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@router.delete(
    "/{place_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a POI by ID"
)
def delete_favourable_place(
    place_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
):
    """
    Delete a POI owned by the current user.
    """
    place = db.get(FavourablePlace, place_id)
    if not place or place.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="POI not found or unauthorized"
        )
    db.delete(place)
    db.commit()
