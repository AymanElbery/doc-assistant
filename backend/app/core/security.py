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
        
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to Keycloak. Make sure Keycloak service is running."
        )

async def verify_token_string(token: str) -> dict:
    """
    Verify JWT token string and return payload.
    Used for both header and query parameter authentication.
    """
    try:
        public_key = get_keycloak_public_key()
        
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={"verify_aud": False}
        )
        
        logger.info(f"Token verified for user: {payload.get('preferred_username', 'unknown')}")
        return payload
    
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token from Keycloak"""
    return await verify_token_string(credentials.credentials)