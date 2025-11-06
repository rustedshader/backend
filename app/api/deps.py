from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.core.config import settings
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.database.tracking_device import TrackingDevice
from typing import Optional


# Hardcoded API keys for live location tracking
# TODO: Move these to environment variables or database in production
VALID_LOCATION_API_KEYS = {
    "loc_api_key_001_tracking_device_alpha",
    "loc_api_key_002_tracking_device_beta",
    "loc_api_key_003_mobile_app_integration",
    "loc_api_key_004_iot_sensor_network",
    "loc_api_key_005_emergency_services",
}


oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_schema), db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        email = email
    except JWTError:
        raise credentials_exception

    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )
    return current_user


async def get_current_guide_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current user if they are a guide.
    """
    if current_user.role != "guide":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current user if they are an admin.
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_current_super_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current user if they are a super admin.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def authenticate_tracking_device(
    x_api_key: str = Header(..., alias="X-API-Key"), db: Session = Depends(get_db)
) -> TrackingDevice:
    """
    Dependency to authenticate tracking device using API key.

    Args:
        x_api_key: API key from the X-API-Key header
        db: Database session

    Returns:
        TrackingDevice: The authenticated tracking device

    Raises:
        HTTPException: If API key is invalid or device is not active
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "API-Key"},
        )

    # Find tracking device by API key
    statement = select(TrackingDevice).where(TrackingDevice.api_key == x_api_key)
    tracking_device = db.exec(statement).first()

    if not tracking_device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )

    return tracking_device


async def verify_location_api_key(
    x_location_api_key: str = Header(None, alias="X-Location-API-Key"),
) -> bool:
    """
    Dependency to verify hardcoded location API keys for live location tracking.

    Args:
        x_location_api_key: API key from the X-Location-API-Key header

    Returns:
        bool: True if API key is valid

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_location_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Location API key is required",
            headers={"WWW-Authenticate": "Location-API-Key"},
        )

    if x_location_api_key not in VALID_LOCATION_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid location API key",
            headers={"WWW-Authenticate": "Location-API-Key"},
        )

    return True


async def get_optional_user(
    token: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally get the current authenticated user from JWT token.
    Returns None if no token is provided or token is invalid.
    """
    if not token:
        return None

    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    else:
        return None

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        email = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()

    if user is None or not user.is_active:
        return None

    return user


async def authenticate_with_jwt_or_api_key(
    x_location_api_key: str = Header(None, alias="X-Location-API-Key"),
    authorization: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Dependency to authenticate using either JWT token OR location API key.
    At least one must be provided and valid.

    Args:
        x_location_api_key: API key from the X-Location-API-Key header (optional)
        authorization: JWT token from Authorization header (optional)
        db: Database session

    Returns:
        dict: Dictionary with authentication info:
            - 'auth_type': 'jwt' or 'api_key'
            - 'user': User object (if JWT) or None
            - 'api_key': API key string (if API key) or None

    Raises:
        HTTPException: If neither authentication method is provided or both are invalid
    """
    authenticated = False
    auth_info = {"auth_type": None, "user": None, "api_key": None}

    # Try JWT authentication first
    if authorization:
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]

        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            email = payload.get("sub")
            if email:
                statement = select(User).where(User.email == email)
                user = db.exec(statement).first()
                if user and user.is_active:
                    authenticated = True
                    auth_info["auth_type"] = "jwt"
                    auth_info["user"] = user
        except JWTError:
            pass  # Try API key next

    # If JWT failed or wasn't provided, try API key
    if not authenticated and x_location_api_key:
        if x_location_api_key in VALID_LOCATION_API_KEYS:
            authenticated = True
            auth_info["auth_type"] = "api_key"
            auth_info["api_key"] = x_location_api_key

    # If neither worked, raise error
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either a valid JWT token (Authorization: Bearer <token>) or a valid location API key (X-Location-API-Key: <key>)",
            headers={"WWW-Authenticate": "Bearer, Location-API-Key"},
        )

    return auth_info
