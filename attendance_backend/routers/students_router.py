"""
routers/students_router.py — Admin: add/remove/list students
                              Student: view own profile
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import get_db
from auth import get_current_admin, get_current_student, hash_password
import models

router = APIRouter(prefix="/api/students", tags=["Students"])


class StudentCreate(BaseModel):
    roll_no:  str
    name:     str
    email:    Optional[str] = None
    dept_id:  int
    password: str

class StudentOut(BaseModel):
    id:      int
    roll_no: str
    name:    str
    email:   Optional[str]
    dept_id: int
    dept_name: str = ""

    class Config:
        from_attributes = True


def _to_out(s: models.Student) -> StudentOut:
    return StudentOut(
        id=s.id,
        roll_no=s.roll_no,
        name=s.name,
        email=s.email,
        dept_id=s.dept_id,
        dept_name=s.department.name if s.department else ""
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get("", response_model=List[StudentOut])
def list_students(
    dept_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    q = db.query(models.Student).filter(models.Student.is_active == True)
    if dept_id:
        q = q.filter(models.Student.dept_id == dept_id)
    return [_to_out(s) for s in q.all()]


@router.post("", response_model=StudentOut)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    if db.query(models.Student).filter(
        models.Student.roll_no == payload.roll_no.upper()
    ).first():
        raise HTTPException(status_code=400, detail="Roll number already exists")

    dept = db.query(models.Department).filter(
        models.Department.id == payload.dept_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    student = models.Student(
        roll_no=payload.roll_no.upper(),
        name=payload.name,
        email=payload.email,
        dept_id=payload.dept_id,
        password_hash=hash_password(payload.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return _to_out(student)


@router.delete("/{student_id}")
def remove_student(
    student_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.is_active = False
    db.commit()
    return {"message": f"{student.name} removed"}


# ── Student: own profile ──────────────────────────────────────────────────────

@router.get("/me", response_model=StudentOut)
def my_profile(current: models.Student = Depends(get_current_student)):
    return _to_out(current)