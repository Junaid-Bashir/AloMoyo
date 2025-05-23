from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from app.database.db           import init_db
from app.services.postal_service import PostalService, get_postal_service
from app.services.auth        import get_current_user
from app.core.config          import settings

# ⬇️ Import all routers here ⬇️
from app.routers.auth              import router as auth_router
from app.routers.businesses        import router as businesses_router
from app.routers.favourable_places import router as favourable_places_router
from app.routers.location_shares   import router as location_shares_router
from app.routers.contributions     import router as contributions_router
from app.routers.shares            import router as shares_router
from app.routers.homes             import router as homes_router
from app.routers.roads             import router as roads_router

app = FastAPI(
    title="AloKazi API",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1, "persistAuthorization": True},
)

@app.on_event("startup")
def on_startup():
    init_db()
    app.dependency_overrides[get_postal_service] = lambda: PostalService()

# Public (no JWT)
app.include_router(auth_router)  # /auth/…

# Protected (JWT required)
protected = [Depends(get_current_user)]
app.include_router(businesses_router,         dependencies=protected)
app.include_router(favourable_places_router,  dependencies=protected)
app.include_router(location_shares_router,    dependencies=protected)
app.include_router(contributions_router,      dependencies=protected)
app.include_router(shares_router,             dependencies=protected)
app.include_router(homes_router,              dependencies=protected)
app.include_router(roads_router,              dependencies=protected)
