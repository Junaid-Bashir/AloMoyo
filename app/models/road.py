from sqlmodel import SQLModel, Field
from datetime import datetime

class Road(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    geometry: str
    status: str = Field(default="pending")
    submitted_by: int
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
