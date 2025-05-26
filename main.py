from fastapi import FastAPI, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis

from app.database.db import init_db
from app.services.postal_service import PostalService, get_postal_service
from app.services.auth import get_current_user

# Routers
from app.routers.auth              import router as auth_router
from app.routers.search            import router as search_router
from app.routers.suggestions       import router as suggestions_router
from app.routers.businesses        import router as businesses_router
from app.routers.favourable_places import router as favourable_places_router
from app.routers.location_shares   import router as location_shares_router
from app.routers.contributions     import router as contributions_router
from app.routers.shares            import router as shares_router
from app.routers.homes             import router as homes_router
from app.routers.roads             import router as roads_router
from app.routers.favorites         import router as favorites_router

from app.core.config import settings

app = FastAPI(
    title="AloMoyo API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
    },
)

@app.on_event("startup")
def on_startup():
    # 1) Initialize DB (drops & recreates tables + FTS setup)
    init_db()

    # 2) Inject PostalService for geocoding/postal lookups
    app.dependency_overrides[get_postal_service] = lambda: PostalService()

    # 3) Initialize Redis-backed cache for FastAPI-Cache2
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASS or None,
    )
    FastAPICache.init(
        backend=RedisBackend(redis_client),
        prefix="fastapi-cache"
    )

# ─── PUBLIC ROUTES ─────────────────────────────────────────────────────────────

# Authentication endpoints
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

# Public search & suggestions
app.include_router(
    search_router,
    prefix="/search",
    tags=["Search"],
)
app.include_router(
    suggestions_router,
    prefix="/suggestions",
    tags=["Suggestions"],
)

# ─── PROTECTED ROUTES (JWT required) ───────────────────────────────────────────

protected = [Depends(get_current_user)]

app.include_router(
    businesses_router,
           prefix="/businesses",
    tags=["Businesses"],
    dependencies=protected,
)
app.include_router(
    favourable_places_router,
    prefix="/favourable_places",
    tags=["FavourablePlaces"],
    dependencies=protected,
)
app.include_router(
    location_shares_router,
    prefix="/location_shares",
    tags=["LocationShares"],
    dependencies=protected,
)
app.include_router(
    contributions_router,
    prefix="/contributions",
    tags=["Contributions"],
    dependencies=protected,
)
app.include_router(
    shares_router,
    prefix="/shares",
    tags=["Shares"],
    dependencies=protected,
)
app.include_router(
    homes_router,
    prefix="/homes",
    tags=["Homes"],
    dependencies=protected,
)
app.include_router(
    roads_router,
    prefix="/roads",
    tags=["Roads"],
    dependencies=protected,
)
app.include_router(
    favorites_router,
    prefix="/favorites",
    tags=["Favorites"],
    dependencies=protected,
)
