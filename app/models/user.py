from sqlmodel import SQLModel, Field
from app.core.security import hash_password, verify_password

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str
    is_admin: bool = Field(default=False)
    country_code: str  = Field(default="ug", nullable=False, index=True)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return hash_password(password)
