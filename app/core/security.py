import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"
PASSWORD_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, expected_hex = encoded.split("$", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return hmac.compare_digest(actual, expected)


def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=get_settings().access_token_expire_minutes
    )
    key = get_settings().secret_key.get_secret_value()
    return jwt.encode({"sub": subject, "exp": expires}, key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    key = get_settings().secret_key.get_secret_value()
    payload = jwt.decode(token, key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdecimal():
        raise JWTError("Invalid token subject.")
    return int(subject)
