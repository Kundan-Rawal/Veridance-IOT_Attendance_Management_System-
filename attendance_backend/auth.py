"""
auth.py — JWT creation, verification, password hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
import models

JWT_SECRET    = os.getenv("JWT_SECRET", "fallback_secret_change_me")
PI_API_KEY    = os.getenv("PI_API_KEY", "")
ALGORITHM     = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8   # 8 hours

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── Dependency: current admin ─────────────────────────────────────────────────

def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("role") != "admin":
        raise credentials_exception
    admin = db.query(models.Admin).filter(
        models.Admin.id == payload.get("sub")
    ).first()
    if not admin or not admin.is_active:
        raise credentials_exception
    return admin


# ── Dependency: current student ───────────────────────────────────────────────

def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Student:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )
    payload = decode_token(token)
    if not payload or payload.get("role") != "student":
        raise credentials_exception
    student = db.query(models.Student).filter(
        models.Student.id == payload.get("sub")
    ).first()
    if not student or not student.is_active:
        raise credentials_exception
    return student


# ── Dependency: Pi device API key ────────────────────────────────────────────

def verify_pi_key(x_api_key: str = Header(...)):
    if not PI_API_KEY:
        raise HTTPException(status_code=500, detail="PI_API_KEY not configured on server")
    if x_api_key != PI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Pi API key")
    return True