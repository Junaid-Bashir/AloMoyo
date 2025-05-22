# File: app/models/location_share.py

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class LocationShare(SQLModel, table=True):
    __tablename__ = "locationshare"

    id: Optional[int] = Field(default=None, primary_key=True)
    latitude: float
    longitude: float
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    digital_address: str

    # Enrichment fields – all nullable
    code: Optional[str] = Field(default=None)
    postal_code: Optional[str] = Field(default=None)
    district_name: Optional[str] = Field(default=None)
    road_name: Optional[str] = Field(default=None)
    house_no: Optional[str] = Field(default=None)
    full_address: Optional[str] = Field(default=None)
