from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.controllers.booking_controller import router as booking_router
from src.controllers.slot_controller import router as slot_router
from src.exceptions.handlers import register_exception_handlers
from src.middleware.api_key_auth import APIKeyAuthMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="RESTful API for clinic appointment scheduling, booking management, and concurrency-safe reservations.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend clients (development: allow all origins, disable credentials for wildcard compliance)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enforce API Key authentication via header X-API-Key (exempting docs, health, etc.)
app.add_middleware(APIKeyAuthMiddleware)

# Register custom exception handlers for uniform error format: {"error": "..."}
register_exception_handlers(app)

# Register controllers
app.include_router(slot_router)
app.include_router(booking_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
