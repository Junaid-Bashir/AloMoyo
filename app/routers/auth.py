from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.database.db import get_db
from app.services.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.schemas import SignupModel, TokenModel, MeModel
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MeModel, status_code=status.HTTP_201_CREATED)
def register(
    payload: SignupModel = Body(...),
    db: Session = Depends(get_db)
) -> MeModel:
    """
    Register a new user and return their profile.
    """
    user = create_user(db, payload.username, payload.email, payload.password)
    return MeModel(
        id=user.id,
        username=user.name,
        email=user.email,
        is_admin=user.is_admin,
        country_code=user.country_code
    )


@router.post("/login", response_model=TokenModel)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenModel:
    """
    Authenticate a user and return a JWT.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenModel(access_token=access_token, token_type="bearer")


@router.post("/forgot-password")
def forgot_password(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Public endpoint to trigger a password reset email.
    """
    # (your email‐sending logic here)
    return {"msg": "If that email is registered, a reset link has been sent"}


@router.get("/me", response_model=MeModel)
def me(
    current_user: User = Depends(get_current_user)
) -> MeModel:
    """
    Return the current authenticated user's profile.
    """
    return MeModel(
        id=current_user.id,
        username=current_user.name,
        email=current_user.email,
        is_admin=current_user.is_admin,
        country_code=current_user.country_code
    )
