"""
routers/attendance_router.py
  - Pi device posts attendance here (API key auth)
  - Admin can view/edit/export attendance
  - Student can view own attendance
"""
import csv
import io
from datetime import date, time as dtime, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import get_current_admin, get_current_student, verify_pi_key
import models

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class MarkRequest(BaseModel):
    roll_no:   str
    name:      str
    dept:      str
    date:      str   # YYYY-MM-DD
    time:      str   # HH:MM:SS
    status:    str = "PRESENT"

class AttendanceOut(BaseModel):
    id:         int
    roll_no:    str
    name:       str
    dept_name:  str
    date:       str
    time:       str
    status:     str
    marked_by:  str


class AdminEditRequest(BaseModel):
    status: str   # PRESENT, ABSENT, LEAVE


# ── Pi device: mark attendance ────────────────────────────────────────────────

@router.post("/mark")
def mark_attendance(
    payload: MarkRequest,
    db: Session = Depends(get_db),
    _=Depends(verify_pi_key)
):
    student = db.query(models.Student).filter(
        models.Student.roll_no == payload.roll_no.upper(),
        models.Student.is_active == True
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail=f"Student {payload.roll_no} not found")

    # Parse date and time
    try:
        att_date = date.fromisoformat(payload.date)
        att_time = dtime.fromisoformat(payload.time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    # Check duplicate
    existing = db.query(models.Attendance).filter(
        models.Attendance.student_id == student.id,
        models.Attendance.date == att_date
    ).first()

    if existing:
        return {"message": "Already marked", "status": existing.status}

    # Create record
    att = models.Attendance(
        student_id=student.id,
        date=att_date,
        time=att_time,
        status=payload.status.upper(),
        marked_by="DEVICE"
    )
    db.add(att)
    db.commit()
    return {"message": "Attendance marked", "student": student.name, "date": str(att_date)}


# ── Admin: view all attendance ────────────────────────────────────────────────

@router.get("/admin", response_model=List[AttendanceOut])
def admin_view_attendance(
    dept_id:    Optional[int]  = Query(None),
    date_from:  Optional[str]  = Query(None),
    date_to:    Optional[str]  = Query(None),
    roll_no:    Optional[str]  = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    q = db.query(models.Attendance).join(models.Student).join(models.Department)

    if dept_id:
        q = q.filter(models.Student.dept_id == dept_id)
    if roll_no:
        q = q.filter(models.Student.roll_no == roll_no.upper())
    if date_from:
        q = q.filter(models.Attendance.date >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(models.Attendance.date <= date.fromisoformat(date_to))

    records = q.order_by(models.Attendance.date.desc()).all()
    return [
        AttendanceOut(
            id=r.id,
            roll_no=r.student.roll_no,
            name=r.student.name,
            dept_name=r.student.department.name,
            date=str(r.date),
            time=str(r.time),
            status=r.status,
            marked_by=r.marked_by,
        )
        for r in records
    ]


# ── Admin: edit one record ────────────────────────────────────────────────────

@router.patch("/admin/{att_id}")
def edit_attendance(
    att_id: int,
    payload: AdminEditRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    att = db.query(models.Attendance).filter(models.Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Record not found")
    att.status    = payload.status.upper()
    att.marked_by = "ADMIN"
    db.commit()
    return {"message": "Updated", "status": att.status}


# ── Admin: mark absent for a date (fill in missing students) ─────────────────

@router.post("/admin/fill-absent")
def fill_absent(
    target_date: str = Query(...),
    dept_id:     Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    att_date = date.fromisoformat(target_date)
    q = db.query(models.Student).filter(models.Student.is_active == True)
    if dept_id:
        q = q.filter(models.Student.dept_id == dept_id)
    students = q.all()

    marked = 0
    for s in students:
        exists = db.query(models.Attendance).filter(
            models.Attendance.student_id == s.id,
            models.Attendance.date == att_date
        ).first()
        if not exists:
            db.add(models.Attendance(
                student_id=s.id,
                date=att_date,
                time=dtime(0, 0, 0),
                status="ABSENT",
                marked_by="ADMIN"
            ))
            marked += 1
    db.commit()
    return {"message": f"Marked {marked} student(s) absent for {target_date}"}


# ── Admin: export CSV ─────────────────────────────────────────────────────────

@router.get("/admin/export")
def export_csv(
    dept_id:   Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    q = db.query(models.Attendance).join(models.Student).join(models.Department)
    if dept_id:
        q = q.filter(models.Student.dept_id == dept_id)
    if date_from:
        q = q.filter(models.Attendance.date >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(models.Attendance.date <= date.fromisoformat(date_to))

    records = q.order_by(models.Attendance.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Department", "Date", "Time", "Status", "Marked By"])
    for r in records:
        writer.writerow([
            r.student.roll_no, r.student.name,
            r.student.department.name,
            str(r.date), str(r.time), r.status, r.marked_by
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"}
    )


# ── Student: own attendance ───────────────────────────────────────────────────

@router.get("/me", response_model=List[AttendanceOut])
def my_attendance(
    current: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    records = db.query(models.Attendance).filter(
        models.Attendance.student_id == current.id
    ).order_by(models.Attendance.date.desc()).all()

    total   = len(records)
    present = sum(1 for r in records if r.status in ("PRESENT", "LEAVE"))
    pct     = round((present / total * 100), 1) if total else 0

    return [
        AttendanceOut(
            id=r.id,
            roll_no=current.roll_no,
            name=current.name,
            dept_name=current.department.name,
            date=str(r.date),
            time=str(r.time),
            status=r.status,
            marked_by=r.marked_by,
        )
        for r in records
    ]


@router.get("/me/summary")
def my_summary(
    current: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    records = db.query(models.Attendance).filter(
        models.Attendance.student_id == current.id
    ).all()
    total   = len(records)
    present = sum(1 for r in records if r.status == "PRESENT")
    leave   = sum(1 for r in records if r.status == "LEAVE")
    absent  = sum(1 for r in records if r.status == "ABSENT")
    pct     = round(((present + leave) / total * 100), 1) if total else 0
    return {
        "total": total, "present": present,
        "leave": leave, "absent": absent,
        "percentage": pct
    }