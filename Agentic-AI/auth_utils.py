import os
import time
import jwt
from fastapi import HTTPException, Header
from testing import JWT_SECRET as K

# Keep your mapping exactly as you requested
SECRET = K


def create_access_token(sub: str, expires_in: int = 3600):
    """Create a signed JWT token with expiration."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + expires_in,
    }

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    # PyJWT older versions sometimes return bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def verify_token(token: str):
    """Verify JWT token and return its payload if valid."""
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        return data

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def get_current_user(authorization: str = Header(None)):
    """
    Extract and validate Bearer token from Authorization header.
    Expected: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    return verify_token(token)
