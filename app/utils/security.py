import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.database.user import RefreshToken
from sqlalchemy.orm import Session


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def hash_identifier(identifier: str) -> str:
    """Hash sensitive identifiers like Aadhar or Passport numbers."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(identifier.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_identifier(identifier: str, hashed_identifier: str) -> bool:
    """Verify a sensitive identifier against its hashed version."""
    return bcrypt.checkpw(identifier.encode("utf-8"), hashed_identifier.encode("utf-8"))


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: int | None = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


async def store_refresh_token(
    db: Session, user_id: int, token: str, expires_delta: int
):
    try:
        expires_at = int(
            (datetime.utcnow() + timedelta(seconds=expires_delta)).timestamp()
        )
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token
    except Exception as e:
        db.rollback()
        raise e
