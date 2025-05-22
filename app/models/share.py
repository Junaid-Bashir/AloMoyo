from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum

class ShareType(str, Enum):
    business         = "business"
    home             = "home"
    favourable_place = "favourable_place"

class Share(SQLModel, table=True):
    id:            int | None    = Field(default=None, primary_key=True)
    resource_type: ShareType
    resource_id:   int
    shared_with:   str           = Field(index=True)   # email of recipient
    shared_by:     int           # user id who shared
    created_at:    datetime      = Field(default_factory=datetime.utcnow)
