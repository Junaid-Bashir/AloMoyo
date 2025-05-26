# app/models/user.py

from datetime import datetime
from sqlmodel import SQLModel, Field
from app.core.security import hash_password, verify_password

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str
    is_admin: bool = Field(default=False)
    country_code: str = Field(default="ug", nullable=False, index=True)

    # ⚡ Email verification fields
    is_verified: bool = Field(default=False, nullable=False)
    verification_code: str | None = Field(default=None, index=True)
    verification_expiry: datetime | None = Field(default=None)

    # ⚡ Password reset fields
    reset_code: str | None = Field(default=None, index=True)
    reset_expiry: datetime | None = Field(default=None)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return hash_password(password)
