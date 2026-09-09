import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import calendar_router
from app.core.config import settings

# Setup standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("braincx")

app = FastAPI(
    title="BrainCX AI Voice Agent API",
    description="Backend service providing Google Calendar availability and booking tools for BrainCX voice agents.",
    version="1.0.0",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    description="Returns the operational status of the service. Does not depend on Google Calendar.",
)
async def health():
    """Health check endpoint to verify that the FastAPI backend is running."""
    return {"status": "ok"}


# Include calendar routes
app.include_router(calendar_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
