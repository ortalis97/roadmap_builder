"""Firebase authentication middleware and dependencies."""

import json

import firebase_admin
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from app.config import get_settings
from app.models.user import User

logger = structlog.get_logger()

# Firebase app instance
_firebase_app: firebase_admin.App | None = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK.

    Call this once during application startup.
    Supports two methods for providing credentials:
    1. GOOGLE_APPLICATION_CREDENTIALS - path to service account JSON file
    2. GOOGLE_APPLICATION_CREDENTIALS_JSON - service account JSON as string

    Skips initialization if credentials not configured.
    """
    global _firebase_app

    if _firebase_app is not None:
        return  # Already initialized

    settings = get_settings()

    # Try JSON string first (preferred for cloud deployment)
    if settings.google_application_credentials_json:
        try:
            cred_dict = json.loads(settings.google_application_credentials_json)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized from JSON credentials")
            return
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to initialize Firebase from JSON", error=str(e))
            raise

    # Fall back to file path
    if settings.google_application_credentials:
        try:
            cred = credentials.Certificate(settings.google_application_credentials)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized from file")
            return
        except Exception as e:
            logger.error("Failed to initialize Firebase from file", error=str(e))
            raise

    logger.warning("Firebase credentials not configured, auth will be disabled")


def is_firebase_initialized() -> bool:
    """Check if Firebase is initialized."""
    return _firebase_app is not None


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Verify Firebase ID token and return decoded claims.

    Raises HTTPException if token is invalid or missing.
    """
    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
) -> User:
    """Get or create user from Firebase token.

    Creates a new user on first login.
    Updates last_seen on subsequent logins.
    """
    firebase_uid = token_data.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing uid",
        )

    # Try to find existing user
    user = await User.find_one(User.firebase_uid == firebase_uid)

    if user is None:
        # Create new user on first login
        logger.info("Creating new user", firebase_uid=firebase_uid)
        user = User(
            firebase_uid=firebase_uid,
            email=token_data.get("email", ""),
            name=token_data.get("name", token_data.get("email", "User")),
            picture=token_data.get("picture"),
        )
        await user.insert()
        logger.info("User created", user_id=str(user.id))
    else:
        # Update last seen
        await user.update_last_seen()

    return user
