"""
routers/departments_router.py — Admin only: add/list/delete departments
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import get_db
from auth import get_current_admin
import models

router = APIRouter(prefix="/api/departments", tags=["Departments"])


class DeptCreate(BaseModel):
    name: str
    code: str

class DeptOut(BaseModel):
    id:   int
    name: str
    code: str
    student_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[DeptOut])
def list_departments(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    depts = db.query(models.Department).all()
    result = []
    for d in depts:
        count = db.query(models.Student).filter(
            models.Student.dept_id == d.id,
            models.Student.is_active == True
        ).count()
        result.append(DeptOut(id=d.id, name=d.name, code=d.code, student_count=count))
    return result


@router.post("", response_model=DeptOut)
def create_department(payload: DeptCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    existing = db.query(models.Department).filter(
        models.Department.code == payload.code.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    dept = models.Department(name=payload.name, code=payload.code.upper())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return DeptOut(id=dept.id, name=dept.name, code=dept.code, student_count=0)


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    count = db.query(models.Student).filter(models.Student.dept_id == dept_id).count()
    if count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {count} student(s) assigned")
    db.delete(dept)
    db.commit()
    return {"message": "Deleted"}