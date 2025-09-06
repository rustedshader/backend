import bcrypt


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
