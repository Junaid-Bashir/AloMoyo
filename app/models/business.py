# File: app/models/business.py

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field



class Business(SQLModel, table=True):
    __tablename__ = "business"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    short_description: Optional[str] = Field(default=None)
    town_or_district: str
    contact_phone: Optional[str] = Field(default=None)
    contact_email: Optional[str] = Field(default=None)
    contact_website: Optional[str] = Field(default=None)
    category: str
    region_code: Optional[str] = Field(default=None)
    latitude: float
    longitude: float
    owner_id: int = Field(foreign_key="user.id")
    average_rating: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    digital_address: str

    # Address/enrichment fields (nullable)
    code: Optional[str] = Field(default=None)
    postal_code: Optional[str] = Field(default=None)
    district_name: Optional[str] = Field(default=None)
    road_name: Optional[str] = Field(default=None)
    house_no: Optional[str] = Field(default=None)
    full_address: Optional[str] = Field(default=None)
