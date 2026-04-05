#!/usr/bin/env python3
"""
train.py  —  Enroll a student's face and retrain the LBPH model.

Controls during capture:
    SPACE  -> capture this frame (only when green box is visible)
    Q      -> quit early

Usage:
    python train.py              # enroll new student
    python train.py --list       # list enrolled students
    python train.py --remove ROLL_NO
    python train.py --retrain    # retrain without enrolling
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

os.chdir(Path(__file__).parent)

from config import MODEL_PATH, LABELS_PATH, DATA_DIR
from modules.lcd_controller import lcd

FACES_DIR    = DATA_DIR / "faces"
SAMPLE_COUNT = 30

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# ── Label helpers ─────────────────────────────────────────────────────────────

def list_enrolled():
    if not LABELS_PATH.exists():
        print("No students enrolled yet.")
        return
    with open(LABELS_PATH, newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        print("No students enrolled yet.")
        return
    print(f"\n{'ID':<6} {'Roll No':<20} {'Name':<25} {'Dept'}")
    print("-" * 65)
    for row in rows:
        if len(row) >= 4:
            print(f"{row[0]:<6} {row[1]:<20} {row[2]:<25} {row[3]}")
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
    print(f"Removed {roll_no}. Retraining model...")
    train_model()


# ── Live capture with preview window ─────────────────────────────────────────

def capture_faces(roll_no: str, name: str) -> int:
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

    saved = 0

    print(f"\n[ENROLL] Camera open.")
    print(f"[ENROLL] SPACE = capture frame (only when GREEN BOX is visible)")
    print(f"[ENROLL] Q     = quit early")
    print(f"[ENROLL] Tip: vary head angle slightly — look left, right, up, down\n")
    lcd.show("Enrolling", name[:16])

    while saved < SAMPLE_COUNT:
        frame = cam.capture_array()
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray_eq = cv2.equalizeHist(gray)

        faces = face_cascade.detectMultiScale(
            gray_eq, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        display      = bgr.copy()
        face_found   = len(faces) > 0
        best_face    = None

        if face_found:
            best_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = best_face
            cv2.rectangle(display, (x, y), (x+w, y+h), (0, 220, 0), 2)
            cv2.putText(display, "Press SPACE to capture",
                        (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2)
        else:
            cv2.putText(display, "No face — look at the camera",
                        (30, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 220), 2)

        # ── Bottom progress bar ───────────────────────────────────────────
        bar_fill = int((saved / SAMPLE_COUNT) * 640)
        cv2.rectangle(display, (0, 458), (640, 480), (30, 30, 30), -1)
        cv2.rectangle(display, (0, 458), (bar_fill, 480), (0, 190, 0), -1)
        cv2.putText(display, f"Captured: {saved} / {SAMPLE_COUNT}",
                    (10, 475), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # ── Top status bar ────────────────────────────────────────────────
        cv2.rectangle(display, (0, 0), (640, 30), (30, 30, 30), -1)
        cv2.putText(display,
                    f"Enrolling: {name}   |   Q = Quit",
                    (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Enrollment - Face Capture", display)
        key = cv2.waitKey(1) & 0xFF

        # Q to quit
        if key in (ord('q'), ord('Q')):
            print(f"\n[ENROLL] Quit early. {saved} samples saved.")
            break

        # SPACE to capture
        if key == ord(' '):
            if face_found and best_face is not None:
                x, y, w, h = best_face
                roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                path = save_dir / f"{saved:03d}.jpg"
                cv2.imwrite(str(path), roi)
                saved += 1

                # Green flash confirmation
                flash = display.copy()
                cv2.rectangle(flash, (0, 0), (640, 480), (0, 255, 0), 8)
                cv2.putText(flash, f"Saved {saved}/{SAMPLE_COUNT}",
                            (190, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 0), 3)
                cv2.imshow("Enrollment - Face Capture", flash)
                cv2.waitKey(300)

                lcd.show(f"Captured {saved}", f"of {SAMPLE_COUNT}")
                print(f"[ENROLL] Saved {saved}/{SAMPLE_COUNT}")
            else:
                print("[ENROLL] No face in frame — position yourself and try again.")

    cam.stop()
    cv2.destroyAllWindows()
    print(f"[ENROLL] Done. {saved} samples saved to: {save_dir}")
    return saved


# ── Train model ───────────────────────────────────────────────────────────────

def train_model():
    if not LABELS_PATH.exists():
        print("[TRAIN] No labels file. Enroll at least one student first.")
        return False

    with open(LABELS_PATH, newline="") as f:
        label_rows = [r for r in csv.reader(f) if r]

    if not label_rows:
        print("[TRAIN] Labels file empty.")
        return False

    id_map = {r[1].upper(): int(r[0]) for r in label_rows}
    faces, ids = [], []

    for roll_no, student_id in id_map.items():
        face_dir = FACES_DIR / roll_no
        if not face_dir.exists():
            print(f"[TRAIN] WARNING: No photos for {roll_no} — skipping.")
            continue
        for img_path in sorted(face_dir.glob("*.jpg")):
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces.append(img)
                ids.append(student_id)

    if not faces:
        print("[TRAIN] No face images found.")
        return False

    print(f"[TRAIN] Training on {len(faces)} images across {len(id_map)} student(s)...")
    lcd.show("Training...", "Please wait")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(ids))
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    recognizer.save(str(MODEL_PATH))

    print(f"[TRAIN] Model saved -> {MODEL_PATH}")
    lcd.show("Model Ready!", f"{len(id_map)} student(s)")
    return True


# ── Enroll flow ───────────────────────────────────────────────────────────────

def enroll():
    print("\n" + "=" * 50)
    print("  STUDENT ENROLLMENT")
    print("=" * 50)

    name = input("Full name      : ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    roll_no = input("Roll number    : ").strip().upper()
    if not roll_no:
        print("Roll number cannot be empty.")
        return

    if roll_exists(roll_no):
        print(f"\nERROR: {roll_no} already enrolled.")
        print("Use --remove ROLL_NO first to re-enroll.")
        return

    dept = input("Department     : ").strip() or "General"

    print(f"\nEnrolling: {name} | {roll_no} | {dept}")
    confirm = input("Confirm? (y/n) : ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    student_id = get_next_id()
    append_label(student_id, roll_no, name, dept)

    print("\nCamera opens in 3 seconds...")
    for i in (3, 2, 1):
        print(f"  {i}...")
        time.sleep(1)

    saved = capture_faces(roll_no, name)

    if saved == 0:
        print("No samples captured. Removing label entry.")
        remove_student(roll_no)
        return

    if saved < SAMPLE_COUNT:
        print(f"[WARN] Only {saved}/{SAMPLE_COUNT} samples captured.")
        print("       Consider re-enrolling for better accuracy.")

    print("\nRetraining model with all enrolled students...")
    ok = train_model()

    if ok:
        print(f"\n[OK] {name} enrolled successfully (ID {student_id}).")
        lcd.show("Enrolled!", name[:16])
    else:
        print("\n[FAIL] Training failed. Check errors above.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Attendance enrollment tool")
    parser.add_argument("--list",    action="store_true", help="List enrolled students")
    parser.add_argument("--remove",  metavar="ROLL_NO",   help="Remove a student")
    parser.add_argument("--retrain", action="store_true", help="Retrain without enrolling")
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