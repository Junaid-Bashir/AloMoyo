# File: app/schemas.py

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

# --------------------------
# Authentication Schemas
# --------------------------
from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupModel(BaseModel):
    username: str
    email: str
    password: str

class VerificationModel(BaseModel):
    email: str
    code: str

class ForgotPasswordModel(BaseModel):
    email: EmailStr

class ResetPasswordModel(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeModel(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    country_code: Optional[str]
    is_verified: bool

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

# --------------------------
# Search Result Schema
# --------------------------

class SearchResultModel(BaseModel):
    id: int
    name: str
    short_description: Optional[str] = None
    latitude: float
    longitude: float
    average_rating: Optional[float] = None
    distance_m: Optional[float] = None

    class Config:
        from_attributes = True
    
class SearchItem(BaseModel):
    id: int
    name: str
    short_description: Optional[str] = None
    latitude: float
    longitude: float
    average_rating: Optional[float] = None
    distance_m: Optional[float] = None
    type: str                  # "business" or "poi"
    detail_url: str            # link to /businesses/{id} or /favourable_places/{id}
    map_url: Optional[str]     # front-end map link template

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    facets: Any                 # e.g. {"categories": [...], "town_slugs": [...]}
    items: List[SearchItem]


# --------------------------
# Favorites Schemas
# --------------------------

# app/schemas.py

from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    resource_type: str
    resource_id: int

class FavoriteRead(BaseModel):
    id: int
    user_id: int
    resource_type: str
    resource_id: int

    class Config:
        orm_mode = True

# --------------------------
# Suggestion Schemas
# --------------------------

from pydantic import BaseModel

class Suggestion(BaseModel):
    id: int
    name: str
    type: str   # e.g. "business" or "poi"

    class Config:
        orm_mode = True


# --------------------------
# Update business Schemas
# --------------------------

class BusinessUpdate(BaseModel):
    name:            Optional[str] = None
    short_description: Optional[str] = None
    town_or_district: Optional[str] = None
    contact_phone:    Optional[str] = None
    contact_email:    Optional[str] = None
    contact_website:  Optional[str] = None
    category:         Optional[str] = None
    region_code:      Optional[str] = None
    latitude:         Optional[float] = None
    longitude:        Optional[float] = None
    country_slug:     Optional[str] = None
    town_slug:        Optional[str] = None

    # --------------------------
# Favorite Update Schema
# --------------------------
class FavoriteUpdate(BaseModel):
    resource_type: Optional[str] = None
    resource_id:   Optional[int]   = None


# --------------------------
# Favourable Place Update Schema
# --------------------------
class FavourablePlaceUpdate(BaseModel):
    label:             Optional[str] = None
    short_description: Optional[str] = None
    town_or_district:  Optional[str] = None
    latitude:          Optional[float] = None
    longitude:         Optional[float] = None
    country_slug:      Optional[str] = None
    town_slug:         Optional[str] = None

# --------------------------

# --------------------------
# Home Update Schema
# --------------------------
class HomeUpdate(BaseModel):
    title:           Optional[str]   = None
    latitude:        Optional[float] = None
    longitude:       Optional[float] = None
    country_slug:    Optional[str]   = None
    town_slug:       Optional[str]   = None

# --------------------------

# --------------------------
# LocationShare Update Schema
# --------------------------
class LocationShareUpdate(BaseModel):
    latitude:      Optional[float] = None
    longitude:     Optional[float] = None
    country_slug:  Optional[str]   = None
    town_slug:     Optional[str]   = None

# --------------------------
# --------------------------
# Road Update Schema
# --------------------------
class RoadUpdate(BaseModel):
    name:     Optional[str] = None
    geometry: Optional[str] = None
    status:   Optional[str] = None


# --------------------------
# Share Update Schema
# --------------------------
class ShareUpdate(BaseModel):
    target_email: str

# --------------------------
# Contribution Update Schema
# --------------------------
class ContributionUpdate(BaseModel):
    wkt: Optional[str] = Field(None, description="New WKT POINT string")