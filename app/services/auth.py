# app/services/auth.py

from datetime import datetime, timedelta
import random
import string
from typing import Optional
from urllib.parse import quote_plus

import smtplib
from email.message import EmailMessage

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.config import settings
from app.database.db import get_db
from app.models.user import User

# Load settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# HTTP Bearer scheme for protecting endpoints
bearer_scheme = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    stmt = select(User).where(or_(User.email == username, User.name == username))
    user = db.exec(stmt).first()
    if not user or not User.verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, username: str, email: str, password: str) -> User:
    user = User(
        name=username,
        email=email,
        hashed_password=User.hash_password(password),
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def generate_verification_code(db: Session, user: User) -> str:
    code = "".join(random.choices(string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=15)
    user.verification_code = code
    user.verification_expiry = expiry
    db.add(user)
    db.commit()
    db.refresh(user)
    return code


def send_verification_email(email: str, code: str) -> None:
    """
    Send the verification code via SMTP with a clickable, URL-encoded link.
    """
    base = str(settings.APP_BASE_URL).rstrip("/")
    e = quote_plus(email)
    link = f"{base}/auth/verify-email?email={e}&code={code}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your AloMoyo account"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email
    msg.set_content(
        f"Welcome to AloMoyo!\n\n"
        f"Please verify your email by clicking the link below:\n\n"
        f"{link}\n\n"
        f"Or enter this code in the app: {code}\n\n"
        f"This link and code expire in 15 minutes."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)


def generate_reset_code(db: Session, user: User) -> str:
    code = "".join(random.choices(string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=30)
    user.reset_code = code
    user.reset_expiry = expiry
    db.add(user)
    db.commit()
    db.refresh(user)
    return code


def send_reset_email(email: str, code: str) -> None:
    """
    Send the password reset code via SMTP with a clickable, URL-encoded link.
    """
    base = str(settings.APP_BASE_URL).rstrip("/")
    e = quote_plus(email)
    link = f"{base}/auth/reset-password?email={e}&code={code}"

    msg = EmailMessage()
    msg["Subject"] = "Reset your AloMoyo password"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email
    msg.set_content(
        f"You requested a password reset.\n\n"
        f"Reset your password by clicking the link below:\n\n"
        f"{link}\n\n"
        f"Or enter this code in the app: {code}\n\n"
        f"This link and code expire in 30 minutes."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)


def reset_password(db: Session, email: str, code: str, new_password: str) -> None:
    stmt = select(User).where(User.email == email)
    user = db.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.reset_code or user.reset_code != code or not user.reset_expiry or user.reset_expiry < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset code")
    user.hashed_password = User.hash_password(new_password)
    user.reset_code = None
    user.reset_expiry = None
    db.add(user)
    db.commit()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = creds.credentials
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise exc
    except JWTError:
        raise exc
    user = db.get(User, int(user_id))
    if not user:
        raise exc
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
