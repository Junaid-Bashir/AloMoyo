# app/main.py

from fastapi import FastAPI
from app.database.db import init_db
from app.services.postal_service import PostalService, get_postal_service

# Core routers (each already has its own .prefix)
from app.routers.auth import router as auth_router
from app.routers.businesses import router as businesses_router
from app.routers.favourable_places import router as favourable_places_router

# Feature routers
from app.routers.location_shares import router as location_shares_router
from app.routers.contributions import router as contributions_router
from app.routers.shares import router as shares_router
from app.routers.homes import router as homes_router
from app.routers.roads import router as roads_router

app = FastAPI(
    title="AloKazi API",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
    },
)

@app.on_event("startup")
def on_startup():
    init_db()
    # make PostalService injectable
    app.dependency_overrides[get_postal_service] = lambda: PostalService()

# **NO more prefix=…** here – each router already declared its own
app.include_router(auth_router)               # /auth/…
app.include_router(businesses_router)         # /businesses/…
app.include_router(favourable_places_router)  # /favourable_places/…
app.include_router(location_shares_router)    # /location_shares/…
app.include_router(contributions_router)      # /contributions/…
app.include_router(shares_router)             # /shares/…
app.include_router(homes_router)              # /homes/…
app.include_router(roads_router)              # /roads/…
