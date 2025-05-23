# File: app/schemas.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

# --------------------------
# Authentication Schemas
# --------------------------

class SignupModel(BaseModel):
    username: str
    email: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeModel(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    country_code: Optional[str]

    class Config:
        orm_mode = True



# --------------------------
# Business Schemas
# --------------------------

class BusinessCreate(SQLModel):
    name: str
    short_description: Optional[str] = None
    town_or_district: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_website: Optional[str] = None
    category: str
    region_code: Optional[str] = None
    latitude: float
    longitude: float
    country_slug: Optional[str] = None
    town_slug: Optional[str] = None

class BusinessRead(SQLModel):
    id: int
    name: str
    short_description: Optional[str] = None
    town_or_district: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_website: Optional[str] = None
    category: str
    region_code: Optional[str] = None
    latitude: float
    longitude: float
    owner_id: int
    average_rating: float
    created_at: datetime
    digital_address: str
    code: Optional[str] = None
    postal_code: Optional[str] = None
    district_name: Optional[str] = None
    road_name: Optional[str] = None
    house_no: Optional[str] = None
    full_address: Optional[str] = None

    class Config:
        orm_mode = True


# --------------------------
# Home Schemas
# --------------------------

class HomeCreate(SQLModel):
    title: str
    latitude: float
    longitude: float
    country_slug: Optional[str] = None
    town_slug: Optional[str] = None

class HomeRead(SQLModel):
    id: int
    title: str
    latitude: float
    longitude: float
    owner_id: int
    created_at: datetime
    digital_address: str
    code: Optional[str] = None
    postal_code: Optional[str] = None
    district_name: Optional[str] = None
    road_name: Optional[str] = None
    house_no: Optional[str] = None
    full_address: Optional[str] = None
    average_rating: float

    class Config:
        orm_mode = True


# --------------------------
# Favourable Place (POI) Schemas
# --------------------------

class FavourablePlaceCreate(SQLModel):
    label: str
    short_description: Optional[str] = None
    town_or_district: str
    latitude: float
    longitude: float
    country_slug: Optional[str] = None
    town_slug: Optional[str] = None

class FavourablePlaceRead(SQLModel):
    id: int
    label: str
    short_description: Optional[str] = None
    town_or_district: str
    latitude: float
    longitude: float
    owner_id: int
    created_at: datetime
    digital_address: str
    code: Optional[str] = None
    postal_code: Optional[str] = None
    district_name: Optional[str] = None
    road_name: Optional[str] = None
    house_no: Optional[str] = None
    full_address: Optional[str] = None

    class Config:
        orm_mode = True


# --------------------------
# LocationShare Schemas
# --------------------------

class LocationShareCreate(SQLModel):
    latitude: float
    longitude: float
    country_slug: Optional[str] = None
    town_slug: Optional[str] = None

class LocationShareRead(SQLModel):
    id: int
    latitude: float
    longitude: float
    owner_id: int
    created_at: datetime
    digital_address: str
    code: Optional[str] = None
    postal_code: Optional[str] = None
    district_name: Optional[str] = None
    road_name: Optional[str] = None
    house_no: Optional[str] = None
    full_address: Optional[str] = None
    share_url: Optional[str] = None
    qr_code: Optional[str] = None

    class Config:
        orm_mode = True


# --------------------------
# Contribution Schemas
# --------------------------

class ContributionCreate(SQLModel):
    wkt: str

class ContributionRead(SQLModel):
    id: int
    wkt: str
    submitted_by_user_id: int
    created_at: datetime
    is_approved: bool
    digital_address: Optional[str] = None
    code: Optional[str] = None
    postal_code: Optional[str] = None
    district_name: Optional[str] = None
    road_name: Optional[str] = None
    house_no: Optional[str] = None
    full_address: Optional[str] = None

    class Config:
        orm_mode = True


# --------------------------
# Share Schemas
# --------------------------

class ShareCreate(SQLModel):
    target_email: str
    resource_id: int
    resource_type: str

class ShareRead(SQLModel):
    id: int
    target_email: str
    resource_id: int
    resource_type: str
    owner_id: int
    created_at: datetime
    share_url: str

    class Config:
        orm_mode = True


# Road Schemas (in app/schemas.py)

class RoadCreate(SQLModel):
    name: str
    geometry: str
    status: str

class RoadRead(SQLModel):
    id: int
    name: str
    geometry: str
    status: str

    # Make these optional with defaults so they won't be required
    owner_id:        Optional[int]      = None
    created_at:      Optional[datetime] = None
    digital_address: Optional[str]      = None
    code:            Optional[str]      = None
    postal_code:     Optional[str]      = None
    district_name:   Optional[str]      = None
    road_name:       Optional[str]      = None
    house_no:        Optional[str]      = None
    full_address:    Optional[str]      = None

    class Config:
        orm_mode = True