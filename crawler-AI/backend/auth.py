import hashlib
import base64
import hmac
import json
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User


SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    # Pre-hash using SHA256
    password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    plain = hashlib.sha256(plain.encode()).hexdigest()
    return pwd_context.verify(plain, hashed)


class JWTError(Exception):
    pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _jwt_encode(payload: dict, secret: str) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_data = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_data = _b64url_encode(json.dumps(payload, separators=(",", ":"), default=str).encode())
    signing_input = f"{header_data}.{payload_data}".encode("ascii")
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_data}.{payload_data}.{_b64url_encode(signature)}"


def _jwt_decode(token: str, secret: str) -> dict:
    try:
        header_data, payload_data, signature_data = token.split(".")
        signing_input = f"{header_data}.{payload_data}".encode("ascii")
        expected_signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        actual_signature = _b64url_decode(signature_data)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise JWTError("Invalid token signature")

        header = json.loads(_b64url_decode(header_data))
        if header.get("alg") != ALGORITHM:
            raise JWTError("Unsupported token algorithm")

        payload = json.loads(_b64url_decode(payload_data))
        exp = payload.get("exp")
        if exp:
            expires_at = datetime.fromisoformat(exp)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise JWTError("Token expired")
        return payload
    except (ValueError, json.JSONDecodeError, TypeError):
        raise JWTError("Invalid token")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=100)
    to_encode.update({"exp": expire.isoformat()})
    return _jwt_encode(to_encode, SECRET_KEY)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    try:
         payload = _jwt_decode(token, SECRET_KEY)
         print("Decoded JWT payload:", payload)
         email = payload.get("sub")
         user = db.query(User).filter(User.email == email).first()
         if user is None:
                raise HTTPException(status_code=401, detail="User not found")
         return email 
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
