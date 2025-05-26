# app/routers/auth.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse

from app.database.db import get_db
from app.models.user import User
from app.schemas import (
    SignupModel,
    VerificationModel,
    ForgotPasswordModel,
    ResetPasswordModel,
    TokenModel,
    MeModel,
)
from app.services.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    generate_verification_code,
    send_verification_email,
    generate_reset_code,
    send_reset_email,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Register a new user")
def register(
    payload: SignupModel = Body(...),
    db: Session = Depends(get_db),
):
    """
    Creates an unverified user and emails a 6-digit verification code.
    """
    user = create_user(db, payload.username, payload.email, payload.password)
    code = generate_verification_code(db, user)
    send_verification_email(user.email, code)
    return {"msg": "Registered. Verification code sent to email."}


@router.post("/verify-email", status_code=status.HTTP_200_OK, summary="Verify email by code")
def verify_email(
    payload: VerificationModel = Body(...),
    db: Session = Depends(get_db),
):
    """
    Verify email using the 6-digit code.
    """
    stmt = select(User).where(User.email == payload.email)
    user = db.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (
        user.verification_code != payload.code
        or not user.verification_expiry
        or user.verification_expiry < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.is_verified = True
    user.verification_code = None
    user.verification_expiry = None
    db.add(user)
    db.commit()
    return {"msg": "Email verified successfully."}


@router.get("/verify-email", status_code=status.HTTP_200_OK, summary="Verify email via link")
def verify_email_link(
    email: str = Query(...),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Click-handler for the emailed verification link.
    """
    stmt = select(User).where(User.email == email)
    user = db.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (
        user.verification_code != code
        or not user.verification_expiry
        or user.verification_expiry < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user.is_verified = True
    user.verification_code = None
    user.verification_expiry = None
    db.add(user)
    db.commit()
    return {"msg": "Email verified successfully via link."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK, summary="Request password reset")
def forgot_password(
    payload: ForgotPasswordModel = Body(...),
    db: Session = Depends(get_db),
):
    """
    Send a 6-digit reset code if the email exists (always returns 200).
    """
    stmt = select(User).where(User.email == payload.email)
    user = db.exec(stmt).first()
    if user:
        code = generate_reset_code(db, user)
        send_reset_email(user.email, code)
    return {"msg": "If that email exists, a reset code has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, summary="Reset password by code")
def password_reset(
    payload: ResetPasswordModel = Body(...),
    db: Session = Depends(get_db),
):
    """
    Verify reset code and update to a new password.
    """
    reset_password(db, payload.email, payload.code, payload.new_password)
    return {"msg": "Password has been reset successfully."}


@router.get("/reset-password", status_code=status.HTTP_200_OK, summary="Validate reset link")
def reset_password_link(
    email: str = Query(...),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Click-handler for the emailed reset link.
    """
    stmt = select(User).where(User.email == email)
    user = db.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (
        user.reset_code != code
        or not user.reset_expiry
        or user.reset_expiry < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    return {"msg": "Reset link valid. You can POST a new password now."}


@router.post("/login", response_model=TokenModel, summary="Obtain JWT token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login a verified user and get back `access_token`.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or email not verified",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenModel(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=MeModel, summary="Get current user profile")
def me(current_user: User = Depends(get_current_user)) -> MeModel:
    """
    Return the currently authenticated user.
    """
    return MeModel(
        id=current_user.id,
        username=current_user.name,
        email=current_user.email,
        is_admin=current_user.is_admin,
        country_code=current_user.country_code,
        is_verified=current_user.is_verified,
    )
