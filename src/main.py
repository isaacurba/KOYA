from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings

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


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify service availability."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
