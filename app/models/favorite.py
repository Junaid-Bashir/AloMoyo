# app/models/favorite.py

from sqlmodel import SQLModel, Field

class Favorite(SQLModel, table=True):
    id: int | None        = Field(default=None, primary_key=True)
    user_id: int          = Field(foreign_key="user.id", nullable=False)
    resource_type: str    = Field(nullable=False)
    resource_id: int      = Field(nullable=False)
