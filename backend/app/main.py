import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import calendar_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.google_calendar import get_calendar_service

# Setup structured production logging
setup_logging(is_production=settings.is_production)
logger = logging.getLogger("braincx")

app = FastAPI(
    title="BrainCX AI Voice Agent API",
    description="Production backend service providing authenticated Google Calendar availability and booking tools for BrainCX voice agents.",
    version="1.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    """Inject production security headers and track request execution duration."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Response-Time"] = f"{duration_ms}ms"

    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Only log non-health endpoints to reduce logging noise
    if not request.url.path.startswith("/health"):
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean, structured validation errors without raw internal stack details."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors.append({
            "field": field,
            "message": err.get("msg"),
        })
    logger.warning(f"Validation failure on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "reason": "VALIDATION_ERROR",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Prevent unhandled exceptions from leaking internal stack traces."""
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "reason": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


@app.get(
    "/health",
    tags=["system"],
    summary="Health Check",
    description="Returns operational status. Compatible with legacy health checks.",
)
async def health():
    """Health check endpoint to verify that the FastAPI backend is running."""
    return {"status": "ok"}


@app.get(
    "/health/live",
    tags=["system"],
    summary="Liveness Probe",
    description="Container liveness check to verify process responsiveness.",
)
async def health_live():
    """Liveness probe: verifies that the FastAPI process is alive and responsive."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}



@app.get(
    "/health/ready",
    tags=["system"],
    summary="Readiness Probe",
    description="Readiness probe verifying Google Calendar configuration and provider readiness.",
)
async def health_ready():
    """Readiness probe: validates integration readiness before serving traffic."""
    service = get_calendar_service()
    calendar_configured = settings.has_google_credentials

    # In production without mock fallback, require credentials
    if settings.is_production and not calendar_configured and not settings.ENABLE_MOCK_FALLBACK:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unready",
                "reason": "GOOGLE_CREDENTIALS_MISSING",
                "message": "Google Calendar credentials are not configured for production.",
            },
        )

    return {
        "status": "ready",
        "environment": settings.ENVIRONMENT,
        "calendar_live": calendar_configured,
        "mock_fallback_enabled": settings.ENABLE_MOCK_FALLBACK or not settings.is_production,
    }


# Include calendar routes
app.include_router(calendar_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=not settings.is_production)

