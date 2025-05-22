# File: app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from jose import JWTError, jwt

from app.database.db import get_db
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas import SignupModel, TokenModel, MeModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["Auth"])


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Verify username (email) and password, returning the User if valid.
    """
    stmt = select(User).where(User.email == username)
    user = db.exec(stmt).first()
    if not user or not User.verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decode JWT token and return the current User.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError()
    except JWTError:
        raise credentials_exception
    user = db.get(User, int(user_id))
    if not user:
        raise credentials_exception
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.post("/signup", response_model=TokenModel, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupModel = Body(...),
    db: Session = Depends(get_db)
) -> TokenModel:
    """
    Register a new user and return a JWT token.
    """
    # Check for existing email
    stmt = select(User).where(User.email == payload.email)
    if db.exec(stmt).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create the user
    user = User(
        name=payload.username,
        email=payload.email,
        hashed_password=User.hash_password(payload.password)
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already in use"
        )
    db.refresh(user)

    # Issue JWT token
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenModel)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenModel:
    """
    Authenticate user via OAuth2 form data and return a JWT token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=MeModel)
def read_users_me(current_user: User = Depends(get_current_user)) -> MeModel:
    """
    Return information about the currently authenticated user.
    """
    return MeModel(
        id=current_user.id,
        username=current_user.name,
        email=current_user.email,
        is_admin=current_user.is_admin,
        country_code=current_user.country_code
    )
