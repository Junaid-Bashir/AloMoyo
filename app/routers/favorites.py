# File: app/routers/favorites.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlmodel import Session, select
from typing import List

from app.database.db import get_db
from app.models.favorite import Favorite
from app.schemas import FavoriteCreate, FavoriteRead, FavoriteUpdate, MeModel
from app.services.auth import get_current_user

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"],
    dependencies=[Depends(get_current_user)],  # require a valid JWT
)


@router.get(
    "/",
    response_model=List[FavoriteRead],
    summary="List all your favorites",
)
def list_favorites(
    db: Session = Depends(get_db),
    user: MeModel = Depends(get_current_user),
) -> List[FavoriteRead]:
    """
    Return all resources the current user has favorited.
    """
    stmt = select(Favorite).where(Favorite.user_id == user.id)
    return db.exec(stmt).all()


@router.post(
    "/",
    response_model=FavoriteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a resource to your favorites",
)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    user: MeModel = Depends(get_current_user),
) -> FavoriteRead:
    """
    Favorites the given resource (business or POI) for the current user.
    Prevents duplicate favorites.
    """
    exists = db.exec(
        select(Favorite)
        .where(
            Favorite.user_id == user.id,
            Favorite.resource_type == payload.resource_type,
            Favorite.resource_id == payload.resource_id
        )
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already favorited")

    fav = Favorite(user_id=user.id, **payload.dict())
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.get(
    "/{fav_id}",
    response_model=FavoriteRead,
    summary="Get details of a specific favorite",
)
def get_favorite(
    fav_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user: MeModel = Depends(get_current_user),
) -> FavoriteRead:
    """
    Retrieve one favorite by its ID, ensuring it belongs to the current user.
    """
    fav = db.get(Favorite, fav_id)
    if not fav or fav.user_id != user.id:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return fav


@router.patch(
    "/{fav_id}",
    response_model=FavoriteRead,
    summary="Update a favorite",
)
def update_favorite(
    payload: FavoriteUpdate = Body(...),
    fav_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user: MeModel = Depends(get_current_user),
) -> FavoriteRead:
    """
    Modify the resource_type or resource_id of one of the user's favorites.
    """
    fav = db.get(Favorite, fav_id)
    if not fav or fav.user_id != user.id:
        raise HTTPException(status_code=404, detail="Favorite not found")

    updates = payload.dict(exclude_unset=True)
    for key, val in updates.items():
        setattr(fav, key, val)

    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete(
    "/{fav_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a favorite",
)
def remove_favorite(
    fav_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user: MeModel = Depends(get_current_user),
):
    """
    Deletes a favorite by its ID, if it belongs to the current user.
    """
    fav = db.get(Favorite, fav_id)
    if not fav or fav.user_id != user.id:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
