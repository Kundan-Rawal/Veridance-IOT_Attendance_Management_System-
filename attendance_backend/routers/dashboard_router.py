"""
routers/dashboard_router.py — Admin dashboard stats
"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_admin
import models

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard_stats(
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    today = date.today()

    total_students = db.query(models.Student).filter(
        models.Student.is_active == True
    ).count()

    total_depts = db.query(models.Department).count()

    today_present = db.query(models.Attendance).filter(
        models.Attendance.date == today,
        models.Attendance.status == "PRESENT"
    ).count()

    today_absent = db.query(models.Attendance).filter(
        models.Attendance.date == today,
        models.Attendance.status == "ABSENT"
    ).count()

    pending_leaves = db.query(models.Leave).filter(
        models.Leave.status == "PENDING"
    ).count()

    # Per department breakdown
    depts = db.query(models.Department).all()
    dept_stats = []
    for d in depts:
        enrolled = db.query(models.Student).filter(
            models.Student.dept_id == d.id,
            models.Student.is_active == True
        ).count()
        present_today = db.query(models.Attendance).join(models.Student).filter(
            models.Student.dept_id == d.id,
            models.Attendance.date == today,
            models.Attendance.status == "PRESENT"
        ).count()
        dept_stats.append({
            "dept_id":       d.id,
            "dept_name":     d.name,
            "dept_code":     d.code,
            "enrolled":      enrolled,
            "present_today": present_today,
            "percentage":    round((present_today / enrolled * 100), 1) if enrolled else 0
        })

    return {
        "today":           str(today),
        "total_students":  total_students,
        "total_depts":     total_depts,
        "today_present":   today_present,
        "today_absent":    today_absent,
        "pending_leaves":  pending_leaves,
        "dept_breakdown":  dept_stats
    }