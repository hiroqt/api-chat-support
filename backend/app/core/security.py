import logging
from typing import Optional
from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_vapi_auth(
    x_vapi_secret: Optional[str] = Header(None, alias="X-Vapi-Secret"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Authenticate incoming tool call requests from Vapi Voice Cloud.
    Enforces shared secret verification against settings.VAPI_SECRET_TOKEN.
    
    Supports:
    1. Header: X-Vapi-Secret: <token>
    2. Header: Authorization: Bearer <token>
    """
    # If no secret token is configured in environment, allow through (e.g. dev/test)
    # but emit an enterprise warning in production
    if not settings.VAPI_SECRET_TOKEN:
        if settings.is_production:
            logger.warning(
                "SECURITY WARNING: VAPI_SECRET_TOKEN is not configured in production. "
                "Tool endpoints are currently accepting unauthenticated requests."
            )
        return True

    # 1. Verify X-Vapi-Secret custom header
    if x_vapi_secret and x_vapi_secret.strip() == settings.VAPI_SECRET_TOKEN.strip():
        return True

    # 2. Verify Authorization Bearer header
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            if parts[1] == settings.VAPI_SECRET_TOKEN.strip():
                return True

    logger.warning("Rejected unauthorized tool call: invalid or missing Vapi authentication credentials.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Missing or invalid Vapi secret token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
