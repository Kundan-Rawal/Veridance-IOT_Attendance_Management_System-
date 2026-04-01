"""
modules/face_engine.py  —  Face recognition + 3-layer anti-spoofing.

Anti-spoofing layers (no PyTorch / no internet required):
  1. Laplacian variance  — a printed photo is blurry/flat; real faces have texture
  2. Frame-delta motion  — a real face has micro-movements between frames
  3. Eye-blink detection — a photo never blinks

All three must pass for attendance to be marked.
"""
import time
import csv
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from config import (
    MODEL_PATH, LABELS_PATH,
    CONFIDENCE_THRESHOLD,
    FACE_TIMEOUT_SECONDS,
    LIVENESS_LAPLACIAN_THRESHOLD,
    LIVENESS_MOTION_THRESHOLD,
)
from modules.lcd_controller import lcd


# ── Load model ────────────────────────────────────────────────────────────────

def load_model() -> Tuple[Optional[object], dict]:
    """
    Returns (recognizer, label_map) or (None, {}) if no model trained yet.
    label_map: {int_id: roll_no_string}
    """
    if not MODEL_PATH.exists() or not LABELS_PATH.exists():
        print("[FACE] No trained model found. Run train.py first.")
        return None, {}
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(str(MODEL_PATH))
        labels = {}
        with open(LABELS_PATH, newline="") as f:
            for row in csv.reader(f):
                if row:
                    labels[int(row[0])] = row[1]
        print(f"[FACE] Model loaded — {len(labels)} student(s) enrolled.")
        return recognizer, labels
    except Exception as e:
        print(f"[FACE] Model load error: {e}")
        return None, {}


# ── Cascades ──────────────────────────────────────────────────────────────────

_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
_eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

if _eye_cascade.empty():
    print("[FACE] WARNING: Eye cascade missing — blink check disabled.")


# ── Anti-spoofing helpers ─────────────────────────────────────────────────────

def _laplacian_score(gray_roi: np.ndarray) -> float:
    """Higher = more texture = more likely a real face."""
    return float(cv2.Laplacian(gray_roi, cv2.CV_64F).var())


def _motion_score(gray1: np.ndarray, gray2: np.ndarray) -> float:
    """Mean absolute difference between two face ROIs."""
    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
    return float(np.mean(np.abs(gray1.astype(float) - gray2.astype(float))))


# ── Main verification function ────────────────────────────────────────────────

class VerifyResult:
    __slots__ = ("success", "reason")

    def __init__(self, success: bool, reason: str):
        self.success = success
        self.reason  = reason

    def __repr__(self):
        return f"VerifyResult(success={self.success}, reason={self.reason!r})"


def verify_face(picam2, target_roll_no: str,
                recognizer, label_map: dict) -> VerifyResult:
    """
    Capture frames until:
      - the person matching `target_roll_no` is recognised, AND
      - all three anti-spoofing checks pass
    OR the timeout expires.

    Args:
        picam2          : Started Picamera2 instance.
        target_roll_no  : The roll number from the scanned QR.
        recognizer      : Loaded LBPH recognizer.
        label_map       : {int_id: roll_no} dict.

    Returns:
        VerifyResult with success=True or False + a human-readable reason.
    """
    lcd.show("Look at Camera", "")

    face_casc    = _face_cascade
    eye_casc     = _eye_cascade
    blink_avail  = not eye_casc.empty()

    deadline           = time.time() + FACE_TIMEOUT_SECONDS
    prev_face_gray     = None          # for motion check
    laplacian_passed   = False
    motion_passed      = False
    identity_confirmed = False

    # Blink history: True=eyes open, False=eyes closed
    blink_history: list[bool] = []
    blink_confirmed = not blink_avail   # skip if cascade missing

    while time.time() < deadline:
        frame = picam2.capture_array()
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Equalise histogram to reduce lighting sensitivity
        gray_eq = cv2.equalizeHist(gray)

        faces = face_casc.detectMultiScale(gray_eq, scaleFactor=1.1,
                                           minNeighbors=5, minSize=(80, 80))
        if len(faces) == 0:
            lcd.show("No face found", "Look at Camera")
            prev_face_gray = None
            time.sleep(0.05)
            continue

        # Take the largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        roi_raw = gray[y:y+h, x:x+w]
        roi_eq  = gray_eq[y:y+h, x:x+w]
        roi_200 = cv2.resize(roi_eq, (200, 200))

        # ── Layer 1: Laplacian texture check ──────────────────────────────
        lap = _laplacian_score(roi_raw)
        if lap >= LIVENESS_LAPLACIAN_THRESHOLD:
            laplacian_passed = True
        else:
            print(f"[ANTI-SPOOF] Laplacian too low: {lap:.1f} "
                  f"(threshold {LIVENESS_LAPLACIAN_THRESHOLD}) — possible photo")
            lcd.show("Liveness Fail", "Move closer")
            prev_face_gray = roi_raw.copy()
            time.sleep(0.05)
            continue

        # ── Layer 2: Motion check ─────────────────────────────────────────
        if prev_face_gray is not None:
            mot = _motion_score(prev_face_gray, roi_raw)
            if mot >= LIVENESS_MOTION_THRESHOLD:
                motion_passed = True
            else:
                print(f"[ANTI-SPOOF] Motion too low: {mot:.2f} — possible static image")
        prev_face_gray = roi_raw.copy()

        # ── Layer 3: Blink detection ──────────────────────────────────────
        if blink_avail and not blink_confirmed:
            eyes = eye_casc.detectMultiScale(roi_eq, 1.1, 4)
            has_eyes = len(eyes) >= 1
            blink_history.append(has_eyes)
            if len(blink_history) > 12:
                blink_history.pop(0)
            if len(blink_history) == 12:
                # Pattern: open → closed → open  (indices roughly 0-3, 4-7, 8-11)
                open_start  = any(blink_history[0:4])
                eyes_closed = not any(blink_history[4:8])
                open_end    = any(blink_history[8:12])
                if open_start and eyes_closed and open_end:
                    blink_confirmed = True
                    print("[ANTI-SPOOF] Blink detected ✓")

        # ── Identity check ────────────────────────────────────────────────
        try:
            pred_id, conf = recognizer.predict(roi_200)
            pred_roll     = label_map.get(pred_id, "")
            print(f"[FACE] pred={pred_roll!r} conf={conf:.1f} target={target_roll_no!r}")

            if pred_roll == target_roll_no and conf < CONFIDENCE_THRESHOLD:
                identity_confirmed = True
        except Exception as e:
            print(f"[FACE] Recognizer error: {e}")

        # ── All layers passed? ────────────────────────────────────────────
        if identity_confirmed and laplacian_passed and motion_passed and blink_confirmed:
            return VerifyResult(True, "All checks passed")

        # Update LCD hint
        if not identity_confirmed:
            lcd.show("Verifying...", "Hold still")
        elif not blink_confirmed:
            lcd.show("Verifying...", "Please blink")

        time.sleep(0.04)

    # ── Timeout — figure out what failed ─────────────────────────────────────
    if not identity_confirmed:
        return VerifyResult(False, "Face not recognised")
    if not laplacian_passed or not motion_passed:
        return VerifyResult(False, "Spoofing detected")
    if not blink_confirmed:
        return VerifyResult(False, "No blink detected")
    return VerifyResult(False, "Timeout")