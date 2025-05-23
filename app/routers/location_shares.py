# File: app/routers/location_shares.py

from io import BytesIO
from datetime import datetime
from typing import List
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import qrcode

from app.database.db             import get_db
from app.models.location_share   import LocationShare
from app.schemas                 import LocationShareCreate, LocationShareRead, MeModel
from app.services.auth import get_current_user
from app.core.codes              import make_human_code
from app.services.postal_service import get_postal_service
from app.services.geocode        import get_road_name
from openlocationcode            import openlocationcode as olc
from app.core.config             import settings

router = APIRouter(prefix="/location_shares", tags=["Location Shares"])

def make_share_url(loc_id: int) -> str:
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/location_shares/{loc_id}"

@router.post("/", response_model=LocationShareRead, status_code=status.HTTP_201_CREATED)
def create_location_share(
    payload: LocationShareCreate,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> LocationShareRead:
    # 1) Plus-code
    da = olc.encode(payload.latitude, payload.longitude)

    # 2) Create & flush
    share = LocationShare(
        latitude=payload.latitude,
        longitude=payload.longitude,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        digital_address=da,
    )
    db.add(share)
    db.flush()

    # 3) Human code -> house_no & code
    human_code = make_human_code(
        payload.country_slug or current_user.country_code,
        payload.town_slug     or "",
        share.id
    )
    share.house_no = share.code = human_code

    # 4) Postal & district
    postal = get_postal_service().nearest(
        payload.latitude, payload.longitude, current_user.country_code
    )
    share.postal_code   = postal.postal_code
    share.district_name = postal.place_name

    # 5) Road name
    share.road_name = get_road_name(payload.latitude, payload.longitude)

    # 6) Full address
    share.full_address = (
        f"{share.road_name}, {share.house_no}, "
        f"{share.postal_code}, {share.district_name}, "
        f"{current_user.country_code.upper()}"
    )

    # 7) Commit & refresh
    db.commit()
    db.refresh(share)

    # 8) Build DTO, share_url, and inline qr_code
    dto = LocationShareRead.from_orm(share)
    dto.share_url = make_share_url(share.id)

    # Generate QR PNG and base64-encode
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(dto.share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    dto.qr_code = f"data:image/png;base64,{b64}"

    return dto

@router.get("/", response_model=List[LocationShareRead])
def list_location_shares(
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> List[LocationShareRead]:
    rows = db.exec(
        select(LocationShare).where(LocationShare.owner_id == current_user.id)
    ).all()

    out: List[LocationShareRead] = []
    for share in rows:
        dto = LocationShareRead.from_orm(share)
        dto.share_url = make_share_url(share.id)

        # regenerate inline QR
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(dto.share_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        dto.qr_code = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

        out.append(dto)
    return out

@router.get("/{loc_id}/qr")
def get_location_qr(
    loc_id: int,
    db: Session = Depends(get_db),
    current_user: MeModel = Depends(get_current_user),
) -> StreamingResponse:
    share = db.get(LocationShare, loc_id)
    if not share or share.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Location not found")

    url = make_share_url(share.id)
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
