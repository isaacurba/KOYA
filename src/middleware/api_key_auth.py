from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.settings import get_settings

EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing API key authentication via the X-API-Key header.

    Exempts public endpoints such as health checks, API docs, and CORS preflight requests.
    Returns HTTP 401 with {"error": "Invalid or missing API key"} on authentication failure.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow exempt documentation and health paths
        path = request.url.path.rstrip("/") or "/"
        if path in EXEMPT_PATHS or path.startswith(("/docs", "/redoc")):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        settings = get_settings()

        if not api_key or api_key != settings.API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key"},
            )

        return await call_next(request)
