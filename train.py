#!/usr/bin/env python3
"""
train.py  —  Enroll a student's face and retrain the LBPH model.

Usage:
    python train.py              # interactive mode (asks for details)
    python train.py --list       # show all enrolled students
    python train.py --remove ROLL_NO   # remove a student and retrain

How it works:
    1. Enter student name, roll number, department
    2. Camera opens — student looks at camera
    3. 30 face photos are captured automatically
    4. Model is retrained on ALL enrolled students
    5. LCD shows confirmation
"""
import sys
import os
import csv
import time
import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np

# ── Make sure we run from the project root ────────────────────────────────────
os.chdir(Path(__file__).parent)

from config import MODEL_PATH, LABELS_PATH, DATA_DIR
from modules.lcd_controller import lcd

FACES_DIR    = DATA_DIR / "faces"
SAMPLE_COUNT = 30          # photos captured per student
SAMPLE_DELAY = 0.15        # seconds between captures


# ── Helpers ───────────────────────────────────────────────────────────────────

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def list_enrolled():
    if not LABELS_PATH.exists():
        print("No students enrolled yet.")
        return
    with open(LABELS_PATH, newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        print("No students enrolled yet.")
        return
    print(f"\n{'ID':<6} {'Roll No':<15} {'Name':<25} {'Dept'}")
    print("─" * 60)
    for row in rows:
        if len(row) >= 4:
            print(f"{row[0]:<6} {row[1]:<15} {row[2]:<25} {row[3]}")
    print()


def get_next_id() -> int:
    if not LABELS_PATH.exists():
        return 0
    with open(LABELS_PATH, newline="") as f:
        rows = [r for r in csv.reader(f) if r]
    return max((int(r[0]) for r in rows), default=-1) + 1


def roll_exists(roll_no: str) -> bool:
    if not LABELS_PATH.exists():
        return False
    with open(LABELS_PATH, newline="") as f:
        return any(r[1].upper() == roll_no.upper()
                   for r in csv.reader(f) if r)


def append_label(student_id: int, roll_no: str, name: str, dept: str):
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LABELS_PATH, "a", newline="") as f:
        csv.writer(f).writerow([student_id, roll_no, name, dept])


def remove_student(roll_no: str):
    if not LABELS_PATH.exists():
        print("No students enrolled.")
        return
    with open(LABELS_PATH, newline="") as f:
        rows = [r for r in csv.reader(f) if r]

    new_rows = [r for r in rows if r[1].upper() != roll_no.upper()]
    if len(new_rows) == len(rows):
        print(f"Roll number {roll_no} not found.")
        return

    with open(LABELS_PATH, "w", newline="") as f:
        csv.writer(f).writerows(new_rows)

    face_dir = FACES_DIR / roll_no.upper()
    if face_dir.exists():
        shutil.rmtree(face_dir)
        print(f"Deleted face photos for {roll_no}")

    print(f"Removed {roll_no}. Retraining model…")
    train_model()


# ── Capture ───────────────────────────────────────────────────────────────────

def capture_faces(roll_no: str, name: str) -> int:
    """
    Open camera, detect faces, save SAMPLE_COUNT grayscale face ROIs.
    Returns number of samples actually saved.
    """
    from picamera2 import Picamera2

    save_dir = FACES_DIR / roll_no.upper()
    save_dir.mkdir(parents=True, exist_ok=True)

    cam = Picamera2()
    cfg = cam.create_preview_configuration(
        main={"size": (640, 480), "format": "XBGR8888"}
    )
    cam.configure(cfg)
    cam.start()
    time.sleep(1)

    print(f"\n[CAPTURE] Camera ready.")
    print(f"[CAPTURE] Look at the camera. Capturing {SAMPLE_COUNT} samples…")
    print("[CAPTURE] Move your head slightly — small tilts help the model.")
    lcd.show("Enrolling", name[:16])

    saved   = 0
    attempt = 0

    while saved < SAMPLE_COUNT:
        attempt += 1
        frame = cam.capture_array()
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)

        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) == 0:
            if attempt % 20 == 0:
                print(f"[CAPTURE] No face detected — please look at the camera.")
                lcd.show("No face found", "Look at camera")
            time.sleep(0.05)
            continue

        # Take the largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))

        path = save_dir / f"{saved:03d}.jpg"
        cv2.imwrite(str(path), roi)
        saved += 1

        pct = int(saved / SAMPLE_COUNT * 100)
        bar = "█" * (saved // 3) + "░" * ((SAMPLE_COUNT - saved) // 3)
        print(f"\r[CAPTURE] {bar} {saved}/{SAMPLE_COUNT} ({pct}%)", end="", flush=True)
        lcd.show(f"Capturing {pct}%", f"{saved}/{SAMPLE_COUNT}")

        time.sleep(SAMPLE_DELAY)

    print()   # newline after progress bar
    cam.stop()
    print(f"[CAPTURE] Done. {saved} samples saved to {save_dir}")
    return saved


# ── Train ─────────────────────────────────────────────────────────────────────

def train_model():
    """Read ALL face photos from data/faces/, train LBPH, save model."""
    if not LABELS_PATH.exists():
        print("[TRAIN] No labels file. Enroll at least one student first.")
        return False

    with open(LABELS_PATH, newline="") as f:
        label_rows = [r for r in csv.reader(f) if r]

    if not label_rows:
        print("[TRAIN] Labels file is empty.")
        return False

    # Build id → roll_no map
    id_map = {r[1].upper(): int(r[0]) for r in label_rows}

    faces, ids = [], []

    for roll_no, student_id in id_map.items():
        face_dir = FACES_DIR / roll_no
        if not face_dir.exists():
            print(f"[TRAIN] WARNING: No photos for {roll_no} — skipping.")
            continue
        imgs = list(face_dir.glob("*.jpg"))
        if not imgs:
            print(f"[TRAIN] WARNING: Empty photo dir for {roll_no} — skipping.")
            continue
        for img_path in imgs:
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces.append(img)
                ids.append(student_id)

    if not faces:
        print("[TRAIN] No face images found. Cannot train.")
        return False

    print(f"[TRAIN] Training on {len(faces)} images across {len(id_map)} student(s)…")
    lcd.show("Training...", "Please wait")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(ids))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    recognizer.save(str(MODEL_PATH))

    print(f"[TRAIN] Model saved → {MODEL_PATH}")
    lcd.show("Model Ready!", f"{len(id_map)} student(s)")
    return True


# ── Enroll flow ───────────────────────────────────────────────────────────────

def enroll():
    print("\n" + "═" * 50)
    print("  STUDENT ENROLLMENT")
    print("═" * 50)

    name = input("Full name      : ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    roll_no = input("Roll number    : ").strip().upper()
    if not roll_no:
        print("Roll number cannot be empty.")
        return

    if roll_exists(roll_no):
        print(f"\nERROR: Roll number {roll_no} is already enrolled.")
        print("Use --remove ROLL_NO first if you want to re-enroll.")
        return

    dept = input("Department     : ").strip()
    if not dept:
        dept = "General"

    print(f"\nEnrolling: {name} | {roll_no} | {dept}")
    confirm = input("Confirm? (y/n) : ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    student_id = get_next_id()
    append_label(student_id, roll_no, name, dept)

    print("\nGet ready — the camera will start in 3 seconds.")
    for i in (3, 2, 1):
        print(f"  {i}…")
        time.sleep(1)

    saved = capture_faces(roll_no, name)

    if saved < SAMPLE_COUNT:
        print(f"[WARN] Only captured {saved}/{SAMPLE_COUNT} samples.")

    print("\nRetraining model with all enrolled students…")
    ok = train_model()

    if ok:
        print(f"\n✅  {name} enrolled successfully (ID {student_id}).")
        lcd.show("Enrolled!", name[:16])
    else:
        print("\n❌  Training failed. Check errors above.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Attendance system enrollment tool")
    parser.add_argument("--list",   action="store_true",  help="List enrolled students")
    parser.add_argument("--remove", metavar="ROLL_NO",    help="Remove a student")
    parser.add_argument("--retrain", action="store_true", help="Retrain model without enrolling")
    args = parser.parse_args()

    if args.list:
        list_enrolled()
    elif args.remove:
        remove_student(args.remove)
    elif args.retrain:
        train_model()
    else:
        enroll()


if __name__ == "__main__":
    main()