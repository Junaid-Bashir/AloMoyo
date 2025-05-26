# File: app/routers/shares.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlmodel import Session, select
from datetime import datetime
from typing import List

from app.database.db import get_db
from app.models.share import Share
from app.schemas import ShareCreate, ShareRead, ShareUpdate, MeModel
from app.services.auth import get_current_user
from app.core.config import settings

router = APIRouter(
    prefix="/shares",
    tags=["Shares"],
    dependencies=[Depends(get_current_user)],  # secure all endpoints
)


def make_share_url(resource_type: str, resource_id: int) -> str:
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/{resource_type}s/{resource_id}"


@router.post(
    "/",
    response_model=ShareRead,
    status_code=status.HTTP_201_CREATED,
    summary="Share one of your resources with someone else"
)
def create_share(
    payload: ShareCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> ShareRead:
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

    return ShareRead(
        id=share.id,
        target_email=share.shared_with,
        resource_id=share.resource_id,
        resource_type=share.resource_type,
        owner_id=share.shared_by,
        created_at=share.created_at,
        share_url=make_share_url(share.resource_type, share.resource_id),
    )


@router.get(
    "/sent",
    response_model=List[ShareRead],
    summary="List shares you have sent"
)
def list_sent_shares(
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> List[ShareRead]:
    rows = db.exec(
        select(Share).where(Share.shared_by == current_user.id)
    ).all()
    return [
        ShareRead(
            id=s.id,
            target_email=s.shared_with,
            resource_id=s.resource_id,
            resource_type=s.resource_type,
            owner_id=s.shared_by,
            created_at=s.created_at,
            share_url=make_share_url(s.resource_type, s.resource_id),
        )
        for s in rows
    ]


@router.get(
    "/received",
    response_model=List[ShareRead],
    summary="List shares sent to you"
)
def list_received_shares(
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> List[ShareRead]:
    rows = db.exec(
        select(Share).where(Share.shared_with == current_user.email)
    ).all()
    return [
        ShareRead(
            id=s.id,
            target_email=s.shared_with,
            resource_id=s.resource_id,
            resource_type=s.resource_type,
            owner_id=s.shared_by,
            created_at=s.created_at,
            share_url=make_share_url(s.resource_type, s.resource_id),
        )
        for s in rows
    ]


@router.get(
    "/{share_id}",
    response_model=ShareRead,
    summary="Get details of a specific share"
)
def get_share(
    share_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> ShareRead:
    share = db.get(Share, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    if share.shared_by != current_user.id and share.shared_with != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to view this share")
    return ShareRead(
        id=share.id,
        target_email=share.shared_with,
        resource_id=share.resource_id,
        resource_type=share.resource_type,
        owner_id=share.shared_by,
        created_at=share.created_at,
        share_url=make_share_url(share.resource_type, share.resource_id),
    )


@router.patch(
    "/{share_id}",
    response_model=ShareRead,
    summary="Update a share's target email"
)
def update_share(
    payload: ShareUpdate = Body(...),
    share_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> ShareRead:
    """
    Allows the sender to change the target_email.
    """
    share = db.get(Share, share_id)
    if not share or share.shared_by != current_user.id:
        raise HTTPException(status_code=404, detail="Share not found or unauthorized")
    share.shared_with = payload.target_email
    db.add(share)
    db.commit()
    db.refresh(share)
    return ShareRead(
        id=share.id,
        target_email=share.shared_with,
        resource_id=share.resource_id,
        resource_type=share.resource_type,
        owner_id=share.shared_by,
        created_at=share.created_at,
        share_url=make_share_url(share.resource_type, share.resource_id),
    )


@router.delete(
    "/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke (delete) a share"
)
def delete_share(
    share_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
):
    """
    Delete a share you sent.
    """
    share = db.get(Share, share_id)
    if not share or share.shared_by != current_user.id:
        raise HTTPException(status_code=404, detail="Share not found or unauthorized")
    db.delete(share)
    db.commit()
