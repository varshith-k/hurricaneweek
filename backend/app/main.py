from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.simulations import router as simulations_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(simulations_router, prefix=settings.api_prefix)

