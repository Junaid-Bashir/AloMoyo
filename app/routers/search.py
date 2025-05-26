from fastapi import APIRouter, Query, Depends, Request
from typing import List, Optional
from sqlmodel import Session, select, text
import math
from urllib.parse import urlencode

from fastapi_cache.decorator import cache

from app.database.db import get_db
from app.models.business import Business
from app.models.favourable_place import FavourablePlace
from app.schemas import SearchResponse, SearchItem

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    dependencies=[],  # public
)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    φ1, φ2 = math.radians(lat1), math.radians(lon1)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get(
    "/",
    response_model=SearchResponse,
    summary="Public FTS-powered search with facets, sorting, pagination"
)
@cache(expire=60)  # cache each unique query+params for 60 seconds
def search_places(
    request: Request,
    query: Optional[str]    = Query(None, description="Text search (uses FTS5)"),
    category: Optional[str] = Query(None),
    town_slug: Optional[str]= Query(None),
    lat: Optional[float]    = Query(None),
    lon: Optional[float]    = Query(None),
    radius: Optional[float] = Query(None, description="Max distance in meters"),
    sort: str               = Query("distance", regex="^(distance|average_rating|name)$"),
    page: int               = Query(1, ge=1),
    per_page: int           = Query(20, ge=1, le=100),
    db: Session             = Depends(get_db),
) -> SearchResponse:
    # 1) “in” syntax override
    q = (query or "").strip()
    if q.lower().count(" in ") == 1 and not town_slug:
        text_part, loc = q.lower().rsplit(" in ", 1)
        q = text_part.strip()
        town_slug = loc.strip().replace(" ", "-")

    # 2) Text matching via FTS
    if q:
        biz_matches = db.exec(text("""
            SELECT b.id AS id, bm.rank AS rank
              FROM business_fts bm
              JOIN business b ON b.id = bm.rowid
             WHERE bm MATCH :q
             ORDER BY rank
        """), {"q": q}).all()
        poi_matches = db.exec(text("""
            SELECT p.id AS id, pm.rank AS rank
              FROM poi_fts pm
              JOIN favourable_place p ON p.id = pm.rowid
             WHERE pm MATCH :q
             ORDER BY rank
        """), {"q": q}).all()
    else:
        biz_ids = db.exec(select(Business.id)).all()
        poi_ids = db.exec(select(FavourablePlace.id)).all()
        biz_matches = [(i, None) for (i,) in biz_ids]
        poi_matches = [(i, None) for (i,) in poi_ids]

    # 3) Fetch models & apply remaining filters
    raw = []
    categories = set()
    towns = set()
    for biz_id, rank in biz_matches:
        biz = db.get(Business, biz_id)
        raw.append((biz, "business", rank))
    for poi_id, rank in poi_matches:
        poi = db.get(FavourablePlace, poi_id)
        raw.append((poi, "poi", rank))

    filtered = []
    for item, kind, rank in raw:
        if not item:
            continue
        if category and getattr(item, "category", None) != category:
            continue
        if town_slug and getattr(item, "town_slug", None) != town_slug:
            continue

        if getattr(item, "category", None):
            categories.add(item.category)
        if getattr(item, "town_slug", None):
            towns.add(item.town_slug)

        if lat is not None and lon is not None:
            dist = haversine(lat, lon, item.latitude, item.longitude)
            if radius is not None and dist > radius:
                continue
        else:
            dist = None

        filtered.append((item, kind, rank, dist))

    # 4) Sorting
    if sort == "distance":
        filtered.sort(key=lambda x: x[3] or float("inf"))
    elif sort == "average_rating":
        filtered.sort(key=lambda x: getattr(x[0], "average_rating", 0.0), reverse=True)
    else:  # name
        filtered.sort(key=lambda x: (getattr(x[0], "name", "") or getattr(x[0], "label", "")).lower())

    # 5) Pagination
    total = len(filtered)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end   = start + per_page

    # 6) Build SearchItem list
    def make_urls(item, kind):
        base = str(request.base_url).rstrip("/")
        if kind == "business":
            detail = f"{base}/businesses/{item.id}"
        else:
            detail = f"{base}/favourable_places/{item.id}"
        map_url = f"https://www.google.com/maps/search/?{urlencode({'api':1,'query':f'{item.latitude},{item.longitude}'})}"
        return detail, map_url

    items = []
    for item, kind, rank, dist in filtered[start:end]:
        detail_url, map_url = make_urls(item, kind)
        items.append(SearchItem(
            id=item.id,
            name=getattr(item, "name", None) or getattr(item, "label", ""),
            short_description=getattr(item, "short_description", None),
            latitude=item.latitude,
            longitude=item.longitude,
            average_rating=getattr(item, "average_rating", None),
            distance_m=dist,
            type=kind,
            detail_url=detail_url,
            map_url=map_url,
        ))

    return SearchResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        facets={"categories": sorted(categories), "town_slugs": sorted(towns)},
        items=items,
    )
