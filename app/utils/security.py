import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.database.user import RefreshToken
from sqlmodel import Session, select
import secrets
import string


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


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def validate_refresh_token(db: Session, refresh_token: str) -> dict | None:
    """Validate a refresh token and return user data if valid."""
    try:
        # First decode the JWT to check if it's valid and not expired
        payload = decode_token(refresh_token)
        if not payload:
            return None

        # Check if the token exists in database and is not revoked
        statement = select(RefreshToken).where(
            RefreshToken.token == refresh_token, ~RefreshToken.is_revoked
        )
        db_token = db.exec(statement).first()

        if not db_token:
            return None

        # Check if token is expired (additional check)
        current_timestamp = int(datetime.utcnow().timestamp())
        if db_token.expires_at < current_timestamp:
            # Mark as revoked if expired
            db_token.is_revoked = True
            db.add(db_token)
            db.commit()
            return None

        return payload

    except Exception:
        return None


async def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
    """Revoke a refresh token."""
    try:
        statement = select(RefreshToken).where(RefreshToken.token == refresh_token)
        db_token = db.exec(statement).first()

        if db_token:
            db_token.is_revoked = True
            db.add(db_token)
            db.commit()
            return True
        return False
    except Exception:
        return False


async def revoke_all_user_tokens(db: Session, user_id: int) -> bool:
    """Revoke all refresh tokens for a user (useful for logout all devices)."""
    try:
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id, ~RefreshToken.is_revoked
        )
        tokens = db.exec(statement).all()

        for token in tokens:
            token.is_revoked = True
            db.add(token)

        db.commit()
        return True
    except Exception:
        return False
