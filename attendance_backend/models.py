"""
models.py — All database table definitions
"""
from sqlalchemy import (
    Column, Integer, String, Date, Time,
    ForeignKey, DateTime, Text, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Department(Base):
    __tablename__ = "departments"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), unique=True, nullable=False)
    code       = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship("Student", back_populates="department")


class Admin(Base):
    __tablename__ = "admins"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, index=True)
    roll_no       = Column(String(50), unique=True, nullable=False, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=True)
    dept_id       = Column(Integer, ForeignKey("departments.id"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    department  = relationship("Department", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")
    leaves      = relationship("Leave", back_populates="student")


class Attendance(Base):
    __tablename__ = "attendance"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date       = Column(Date, nullable=False)
    time       = Column(Time, nullable=False)
    status     = Column(String(20), default="PRESENT")  # PRESENT, ABSENT, LEAVE
    marked_by  = Column(String(20), default="DEVICE")   # DEVICE or ADMIN
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="attendances")


class Leave(Base):
    __tablename__ = "leaves"

    id          = Column(Integer, primary_key=True, index=True)
    student_id  = Column(Integer, ForeignKey("students.id"), nullable=False)
    from_date   = Column(Date, nullable=False)
    to_date     = Column(Date, nullable=False)
    reason      = Column(Text, nullable=False)
    status      = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    admin_note  = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="leaves")