"""
routers/auth_router.py — Login for admin and student
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import verify_password, create_token
import models

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    role:         str
    name:         str


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Try admin first
    admin = db.query(models.Admin).filter(models.Admin.email == form.username).first()
    if admin and verify_password(form.password, admin.password_hash):
        token = create_token({"sub": str(student.id), "role": "student"})
        return TokenResponse(access_token=token, role="admin", name=admin.name)

    # Try student
    student = db.query(models.Student).filter(
        models.Student.roll_no == form.username.upper()
    ).first()
    if student and verify_password(form.password, student.password_hash):
        token = create_token({"sub": student.id, "role": "student"})
        return TokenResponse(access_token=token, role="student", name=student.name)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")