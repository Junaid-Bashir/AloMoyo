# File: app/routers/roads.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.road import Road
from app.schemas import RoadCreate, RoadRead, RoadUpdate, MeModel
from app.services.auth import get_current_user

router = APIRouter(
    prefix="/roads",
    tags=["Roads"],
    dependencies=[Depends(get_current_user)],  # secure all routes
)


@router.post(
    "/",
    response_model=RoadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new road geometry"
)
def create_road(
    payload: RoadCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> RoadRead:
    """
    Create a new road record.
    """
    road = Road(
        **payload.dict(),
        submitted_by=current_user.id,
        submitted_at=datetime.utcnow(),
    )
    db.add(road)
    db.commit()
    db.refresh(road)
    return road


@router.get(
    "/",
    response_model=List[RoadRead],
    summary="List all roads"
)
def list_roads(
    db: Session = Depends(get_db),
) -> List[RoadRead]:
    """
    Retrieve all roads.
    """
    return db.exec(select(Road)).all()


@router.get(
    "/{road_id}",
    response_model=RoadRead,
    summary="Get a single road by ID"
)
def get_road(
    road_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
) -> RoadRead:
    """
    Retrieve one road by its ID.
    """
    road = db.get(Road, road_id)
    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found"
        )
    return road


@router.patch(
    "/{road_id}",
    response_model=RoadRead,
    summary="Update a road by ID"
)
def update_road(
    payload: RoadUpdate = Body(...),
    road_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> RoadRead:
    """
    Partially update a road record.
    """
    road = db.get(Road, road_id)
    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found"
        )
    # (Optionally enforce ownership/admin here)

    updates = payload.dict(exclude_unset=True)
    for key, val in updates.items():
        setattr(road, key, val)

    db.add(road)
    db.commit()
    db.refresh(road)
    return road


@router.delete(
    "/{road_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a road by ID"
)
def delete_road(
    road_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
):
    """
    Delete a road record.
    """
    road = db.get(Road, road_id)
    if not road:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found"
        )
    # (Optionally enforce ownership/admin here)
    db.delete(road)
    db.commit()
