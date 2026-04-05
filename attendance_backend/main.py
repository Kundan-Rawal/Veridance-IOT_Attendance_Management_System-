"""
main.py — FastAPI application entry point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base, SessionLocal
from auth import hash_password
import models

# ── Create all tables ─────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Seed first admin ──────────────────────────────────────────────────────────
def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(models.Admin).first()
        if not existing:
            admin = models.Admin(
                name=os.getenv("ADMIN_NAME", "Administrator"),
                email=os.getenv("ADMIN_EMAIL", "admin@college.edu"),
                password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "Admin@1234")),
            )
            db.add(admin)
            db.commit()
            print(f"[SEED] Admin created: {admin.email}")
        else:
            print(f"[SEED] Admin already exists: {existing.email}")
    finally:
        db.close()

seed_admin()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Attendance System API",
    description="Backend for Raspberry Pi attendance system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your Vercel URL after testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers.auth_router       import router as auth_router
from routers.departments_router import router as dept_router
from routers.students_router   import router as student_router
from routers.attendance_router import router as attendance_router
from routers.leaves_router     import router as leaves_router
from routers.dashboard_router  import router as dashboard_router

app.include_router(auth_router)
app.include_router(dept_router)
app.include_router(student_router)
app.include_router(attendance_router)
app.include_router(leaves_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"status": "Attendance API running", "docs": "/docs"}