# File: app/routers/suggestions.py

from fastapi import APIRouter, Query, Depends
from typing import List
from sqlmodel import Session, text

from app.database.db import get_db
from app.schemas import Suggestion

router = APIRouter(
    prefix="/suggestions",
    tags=["Suggestions"],
    dependencies=[Depends(get_db)],  # still opens DB but no auth
)

@router.get(
    "/",
    response_model=List[Suggestion],
    summary="Autocomplete place names"
)
def suggest(
    q: str = Query(..., min_length=1, description="Prefix to search for"),
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions"),
    db: Session = Depends(get_db),
):
    """
    Returns up to `limit` name suggestions from businesses and POIs
    matching the prefix `q`. Uses SQLite FTS5 prefix search.
    """
    # Business names
    biz_rows = db.exec(text("""
        SELECT b.id, b.name AS text
          FROM business_fts bm
          JOIN business b ON b.id = bm.rowid
         WHERE bm MATCH :query || '*'
         LIMIT :limit
    """), {"query": q, "limit": limit}).all()

    # POI labels
    poi_rows = db.exec(text("""
        SELECT p.id, p.label AS text
          FROM poi_fts pm
          JOIN favourable_place p ON p.id = pm.rowid
         WHERE pm MATCH :query || '*'
         LIMIT :limit
    """), {"query": q, "limit": limit}).all()

    # Merge and dedupe by (id, text)
    seen = set()
    results: List[Suggestion] = []
    for _id, txt in biz_rows + poi_rows:
        key = (txt.lower(), _id)
        if key in seen:
            continue
        seen.add(key)
        results.append(Suggestion(id=_id, text=txt))
        if len(results) >= limit:
            break

    return results
