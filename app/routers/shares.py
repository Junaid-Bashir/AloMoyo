# File: app/routers/shares.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import List

from app.database.db import get_db
from app.models.share import Share
from app.schemas import ShareCreate, ShareRead, MeModel
from app.routers.auth import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/shares", tags=["Shares"])


def make_share_url(resource_type: str, resource_id: int) -> str:
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/{resource_type}s/{resource_id}"


@router.post("/", response_model=ShareRead, status_code=status.HTTP_201_CREATED)
def create_share(
    payload: ShareCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> ShareRead:
    """
    Create a new share. Uses `target_email`, `resource_id`, and `resource_type`
    from the payload, sets shared_by and timestamp, generates share_url,
    and returns the ShareRead DTO.
    """
    # 1) Build and persist Share
    share = Share(
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        shared_with=payload.target_email,
        shared_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    # 2) Generate share_url
    share_url = make_share_url(share.resource_type, share.resource_id)

    # 3) Return DTO manually to align fields
    return ShareRead(
        id=share.id,
        target_email=share.shared_with,
        resource_id=share.resource_id,
        resource_type=share.resource_type,
        owner_id=share.shared_by,
        created_at=share.created_at,
        share_url=share_url,
    )


@router.get("/", response_model=List[ShareRead])
def list_shares(
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> List[ShareRead]:
    """
    List all shares created by the current user.
    """
    rows = db.exec(
        select(Share).where(Share.shared_by == current_user.id)
    ).all()
    out: List[ShareRead] = []
    for share in rows:
        share_url = make_share_url(share.resource_type, share.resource_id)
        out.append(ShareRead(
            id=share.id,
            target_email=share.shared_with,
            resource_id=share.resource_id,
            resource_type=share.resource_type,
            owner_id=share.shared_by,
            created_at=share.created_at,
            share_url=share_url,
        ))
    return out
