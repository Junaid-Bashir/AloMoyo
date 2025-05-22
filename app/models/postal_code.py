# app/models/postal_code.py

from sqlmodel import SQLModel, Field


class PostalCode(SQLModel, table=True):
    id: int | None    = Field(default=None, primary_key=True)
    country_code: str = Field(index=True)   # "UG", "KE", etc.
    postal_code: str  = Field(index=True)   # "9992", "01000", etc.
    place_name: str                     # town or city name
    latitude: float
    longitude: float
