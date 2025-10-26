from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from functools import lru_cache
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

@lru_cache()
def get_keycloak_public_key() -> str:
    """Fetch Keycloak public key for token verification"""
    # Use internal Docker service name
    url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
    
    logger.info(f"Fetching Keycloak public key from: {url}")
    
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        realm_info = response.json()
        
        public_key = realm_info.get('public_key')
        if not public_key:
            raise ValueError("Public key not found in realm info")
        
        formatted_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        logger.info("Successfully fetched Keycloak public key")
        
        return formatted_key
        
    except httpx.ConnectError as e:
        logger.error(f"Connection error to Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to Keycloak at {url}. Make sure Keycloak service is running."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout connecting to Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout connecting to Keycloak"
        )
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Keycloak public key: {str(e)}"
        )

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token from Keycloak"""
    token = credentials.credentials
    
    try:
        public_key = get_keycloak_public_key()
        
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={"verify_aud": False}  # Keycloak doesn't always set aud
        )
        
        logger.info(f"Token verified for user: {payload.get('preferred_username', 'unknown')}")
        return payload
    
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )