from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from .config import Settings, async_get_setting

security = HTTPBearer()


async def verify_jwt_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: Settings = Depends(async_get_setting),
) -> dict:
    """
    Verify JWT token from Authorization header using FastAPI's HTTPBearer.

    Args:
        credentials: HTTP Bearer credentials extracted by HTTPBearer
        settings: Application settings containing JWT keys

    Returns:
        Decoded JWT payload

    Raises:
        HTTPException: 403 if token verification fails
    """
    token = credentials.credentials

    # Try to decode with each configured key
    last_error = None
    for key_id, secret_key in settings.jwt_keys.items():
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=["HS256", "HS384", "HS512"],
            )
            logger.info(f"Token verified successfully with key: {key_id}")
            return payload
        except jwt.InvalidSignatureError:
            last_error = "Invalid token signature"
            continue
        except jwt.ExpiredSignatureError:
            last_error = "Token has expired"
            logger.warning(f"Expired token attempted with key: {key_id}")
            break
        except jwt.InvalidTokenError as e:
            last_error = f"Invalid token: {e!s}"
            logger.warning(f"Invalid token: {e}")
            continue

    # If we get here, all keys failed
    error_msg = last_error or "Token verification failed"
    logger.warning(f"Token verification failed: {error_msg}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_msg,
    )
