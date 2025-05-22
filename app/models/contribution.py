# File: app/models/contribution.py

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Contribution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contrib_type:    Optional[str]    = Field(default=None)
    name:            Optional[str]    = Field(default=None)
    wkt:             str
    description:     Optional[str]    = Field(default=None)
    is_approved:     bool             = Field(default=False)
    submitted_by_user_id: int         = Field(foreign_key="user.id")
    created_at:      datetime         = Field(default_factory=datetime.utcnow)
    digital_address: Optional[str]    = Field(default=None)
    code:            Optional[str]    = Field(default=None)
    postal_code:     Optional[str]    = Field(default=None)
    district_name:   Optional[str]    = Field(default=None)
    road_name:       Optional[str]    = Field(default=None)
    house_no:        Optional[str]    = Field(default=None)
    full_address:    Optional[str]    = Field(default=None)
