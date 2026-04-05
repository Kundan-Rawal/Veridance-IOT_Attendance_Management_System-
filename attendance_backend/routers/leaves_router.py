"""
routers/leaves_router.py
  - Student: apply for leave, view own leaves
  - Admin: view all leaves, approve/reject
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import get_current_admin, get_current_student
import models

router = APIRouter(prefix="/api/leaves", tags=["Leaves"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LeaveApply(BaseModel):
    from_date: str
    to_date:   str
    reason:    str

class LeaveOut(BaseModel):
    id:         int
    student_id: int
    roll_no:    str
    name:       str
    dept_name:  str
    from_date:  str
    to_date:    str
    reason:     str
    status:     str
    admin_note: Optional[str]

class LeaveAction(BaseModel):
    status:     str             # APPROVED or REJECTED
    admin_note: Optional[str]


def _to_out(leave: models.Leave) -> LeaveOut:
    return LeaveOut(
        id=leave.id,
        student_id=leave.student_id,
        roll_no=leave.student.roll_no,
        name=leave.student.name,
        dept_name=leave.student.department.name,
        from_date=str(leave.from_date),
        to_date=str(leave.to_date),
        reason=leave.reason,
        status=leave.status,
        admin_note=leave.admin_note,
    )


# ── Student: apply ────────────────────────────────────────────────────────────

@router.post("/apply", response_model=LeaveOut)
def apply_leave(
    payload: LeaveApply,
    current: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    try:
        from_date = date.fromisoformat(payload.from_date)
        to_date   = date.fromisoformat(payload.to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if to_date < from_date:
        raise HTTPException(status_code=400, detail="to_date must be after from_date")

    leave = models.Leave(
        student_id=current.id,
        from_date=from_date,
        to_date=to_date,
        reason=payload.reason,
        status="PENDING"
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return _to_out(leave)


# ── Student: view own leaves ──────────────────────────────────────────────────

@router.get("/me", response_model=List[LeaveOut])
def my_leaves(
    current: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    leaves = db.query(models.Leave).filter(
        models.Leave.student_id == current.id
    ).order_by(models.Leave.created_at.desc()).all()
    return [_to_out(l) for l in leaves]


# ── Admin: view all leaves ────────────────────────────────────────────────────

@router.get("/admin", response_model=List[LeaveOut])
def admin_view_leaves(
    status:  Optional[str] = Query(None),   # PENDING, APPROVED, REJECTED
    dept_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    q = db.query(models.Leave).join(models.Student).join(models.Department)
    if status:
        q = q.filter(models.Leave.status == status.upper())
    if dept_id:
        q = q.filter(models.Student.dept_id == dept_id)
    leaves = q.order_by(models.Leave.created_at.desc()).all()
    return [_to_out(l) for l in leaves]


# ── Admin: approve or reject ──────────────────────────────────────────────────

@router.patch("/admin/{leave_id}", response_model=LeaveOut)
def action_leave(
    leave_id: int,
    payload:  LeaveAction,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    leave = db.query(models.Leave).filter(models.Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    status = payload.status.upper()
    if status not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Status must be APPROVED or REJECTED")

    leave.status     = status
    leave.admin_note = payload.admin_note

    # If approved — mark attendance as LEAVE for each day in range
    if status == "APPROVED":
        from datetime import timedelta
        current_date = leave.from_date
        while current_date <= leave.to_date:
            existing = db.query(models.Attendance).filter(
                models.Attendance.student_id == leave.student_id,
                models.Attendance.date == current_date
            ).first()
            if existing:
                existing.status    = "LEAVE"
                existing.marked_by = "ADMIN"
            else:
                from datetime import time as dtime
                db.add(models.Attendance(
                    student_id=leave.student_id,
                    date=current_date,
                    time=dtime(0, 0, 0),
                    status="LEAVE",
                    marked_by="ADMIN"
                ))
            current_date += timedelta(days=1)

    db.commit()
    db.refresh(leave)
    return _to_out(leave)