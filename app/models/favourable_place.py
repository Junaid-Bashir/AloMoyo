# File: app/models/favourable_place.py

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class FavourablePlace(SQLModel, table=True):
    __tablename__ = "favourable_place"

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    short_description: Optional[str] = Field(default=None)
    town_or_district: str
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
