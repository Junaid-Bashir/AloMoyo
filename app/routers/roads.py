from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.database.db import get_db
from app.models.road import Road
from app.schemas import RoadCreate, RoadRead, MeModel
from app.services.auth import get_current_user

router = APIRouter(prefix="/roads", tags=["Roads"])


@router.post("/", response_model=RoadRead)
def create_road(
    payload: RoadCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> RoadRead:
    road = Road(
        **payload.dict(),
        submitted_by=current_user.id,
        submitted_at=datetime.utcnow(),
    )
    db.add(road); db.commit(); db.refresh(road)
    return road


@router.get("/", response_model=List[RoadRead])
def list_roads(db: Session = Depends(get_db)) -> List[RoadRead]:
    return db.exec(select(Road)).all()
