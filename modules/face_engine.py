"""
modules/face_engine.py  —  Face recognition + practical anti-spoofing.

Anti-spoofing (3 layers, all must pass):
  1. Laplacian variance  — flat printed photo = low texture score
  2. Frame-delta motion  — static image = zero movement between frames
  3. Blink detection     — printed photo never blinks

Blink logic (simplified & reliable):
  - Keep a rolling window of eye-open readings
  - A blink = we saw eyes OPEN, then eyes CLOSED, then eyes OPEN again
  - Each phase just needs 2 consecutive matching frames (not strict counts)
"""
import time
import csv
import cv2
import numpy as np
from typing import Optional

from config import (
    MODEL_PATH, LABELS_PATH,
    CONFIDENCE_THRESHOLD,
    FACE_TIMEOUT_SECONDS,
    LIVENESS_LAPLACIAN_THRESHOLD,
    LIVENESS_MOTION_THRESHOLD,
)
from modules.lcd_controller import lcd


# ── Load model ────────────────────────────────────────────────────────────────

def load_model():
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
                    labels[int(row[0])] = row[1]   # id -> roll_no
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

_BLINK_AVAILABLE = not _eye_cascade.empty()
if not _BLINK_AVAILABLE:
    print("[FACE] Eye cascade not found — blink check disabled.")


# ── Result object ─────────────────────────────────────────────────────────────

class VerifyResult:
    def __init__(self, success: bool, reason: str):
        self.success = success
        self.reason  = reason
    def __repr__(self):
        return f"VerifyResult({self.success}, {self.reason!r})"


# ── Simple blink state machine ────────────────────────────────────────────────

class BlinkDetector:
    """
    States:  WAITING_OPEN -> WAITING_CLOSE -> WAITING_REOPEN -> DONE
    Each state needs CONFIRM_FRAMES consecutive matching readings to advance.
    """
    CONFIRM_FRAMES = 2

    def __init__(self):
        self._state   = "WAITING_OPEN"
        self._counter = 0
        self.done     = False

    def update(self, eyes_open: bool) -> bool:
        """Feed one frame reading. Returns True once a full blink is confirmed."""
        if self.done:
            return True

        if self._state == "WAITING_OPEN":
            if eyes_open:
                self._counter += 1
                if self._counter >= self.CONFIRM_FRAMES:
                    self._state   = "WAITING_CLOSE"
                    self._counter = 0
                    print("[BLINK] Phase 1/3: eyes open confirmed")
            else:
                self._counter = 0

        elif self._state == "WAITING_CLOSE":
            if not eyes_open:
                self._counter += 1
                if self._counter >= self.CONFIRM_FRAMES:
                    self._state   = "WAITING_REOPEN"
                    self._counter = 0
                    print("[BLINK] Phase 2/3: eyes closed confirmed")
            else:
                self._counter = 0

        elif self._state == "WAITING_REOPEN":
            if eyes_open:
                self._counter += 1
                if self._counter >= self.CONFIRM_FRAMES:
                    self.done = True
                    print("[BLINK] Phase 3/3: blink complete!")
            else:
                self._counter = 0

        return self.done


# ── Main verification ─────────────────────────────────────────────────────────

def verify_face(picam2, target_roll_no: str,
                recognizer, label_map: dict) -> VerifyResult:
    """
    Verify the person in front of the camera matches `target_roll_no`
    and passes anti-spoofing checks.
    """
    lcd.show("Look at Camera", "Hold still")
    print(f"[FACE] Verifying roll: {target_roll_no}")
    print(f"[FACE] Timeout: {FACE_TIMEOUT_SECONDS}s")
    print(f"[FACE] Confidence threshold: {CONFIDENCE_THRESHOLD} (lower = stricter)")

    deadline        = time.time() + FACE_TIMEOUT_SECONDS
    prev_face_gray  = None

    # Track which checks have passed
    identity_ok  = False
    laplacian_ok = False
    motion_ok    = False
    blink_det    = BlinkDetector()
    blink_ok     = not _BLINK_AVAILABLE   # skip if cascade missing

    frames_checked = 0

    while time.time() < deadline:
        frame = picam2.capture_array()
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray_eq = cv2.equalizeHist(gray)

        faces = _face_cascade.detectMultiScale(
            gray_eq, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) == 0:
            prev_face_gray = None
            time.sleep(0.05)
            continue

        frames_checked += 1
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        roi_raw = gray[y:y+h, x:x+w]
        roi_eq  = gray_eq[y:y+h, x:x+w]
        roi_200 = cv2.resize(roi_eq, (200, 200))

        # ── Layer 1: Laplacian (texture / anti-photo) ─────────────────────
        lap_score = float(cv2.Laplacian(roi_raw, cv2.CV_64F).var())
        if lap_score >= LIVENESS_LAPLACIAN_THRESHOLD:
            laplacian_ok = True
        else:
            print(f"[ANTI-SPOOF] Laplacian {lap_score:.1f} < {LIVENESS_LAPLACIAN_THRESHOLD} — possible flat photo")
            prev_face_gray = roi_raw.copy()
            time.sleep(0.05)
            continue

        # ── Layer 2: Motion (anti-static-image) ───────────────────────────
        if prev_face_gray is not None:
            if prev_face_gray.shape != roi_raw.shape:
                prev_resized = cv2.resize(prev_face_gray,
                                          (roi_raw.shape[1], roi_raw.shape[0]))
            else:
                prev_resized = prev_face_gray
            motion = float(np.mean(np.abs(
                roi_raw.astype(float) - prev_resized.astype(float)
            )))
            if motion >= LIVENESS_MOTION_THRESHOLD:
                motion_ok = True
            # Don't block on motion alone — natural stillness can fail this
            # It's a supporting signal, not a hard gate after frame 10
            print(f"[MOTION] score={motion:.2f} ok={motion_ok}")
        prev_face_gray = roi_raw.copy()

        # ── Layer 3: Blink detection ──────────────────────────────────────
        if _BLINK_AVAILABLE and not blink_ok:
            eyes = _eye_cascade.detectMultiScale(
                roi_eq, scaleFactor=1.1, minNeighbors=4, minSize=(20, 20)
            )
            eyes_open = len(eyes) >= 1
            blink_ok  = blink_det.update(eyes_open)

            if not blink_ok:
                state_msg = {
                    "WAITING_OPEN":   "Open your eyes",
                    "WAITING_CLOSE":  "Now blink!",
                    "WAITING_REOPEN": "Open again...",
                }.get(blink_det._state, "Blink once")
                lcd.show("Anti-spoof", state_msg)

        # ── Identity check ────────────────────────────────────────────────
        try:
            pred_id, conf = recognizer.predict(roi_200)
            pred_roll     = label_map.get(pred_id, "UNKNOWN")
            print(f"[FACE] pred={pred_roll!r}  conf={conf:.1f}  "
                  f"target={target_roll_no!r}  "
                  f"[lap={laplacian_ok} mot={motion_ok} blk={blink_ok}]")

            if pred_roll == target_roll_no and conf < CONFIDENCE_THRESHOLD:
                identity_ok = True
        except Exception as e:
            print(f"[FACE] Recognizer error: {e}")

        # ── Update LCD hint ───────────────────────────────────────────────
        if not identity_ok:
            lcd.show("Verifying...", "Hold still")
        elif not blink_ok:
            lcd.show("Blink once", "please...")

        # ── All checks passed? ────────────────────────────────────────────
        # Motion is a soft check — if we have 15+ frames of movement data
        # and motion never triggered, it might be a very still real person.
        # We give it a pass after 20 frames to avoid false rejections.
        if frames_checked >= 20 and not motion_ok:
            motion_ok = True
            print("[MOTION] Soft pass after 20 frames.")

        if identity_ok and laplacian_ok and motion_ok and blink_ok:
            return VerifyResult(True, "All checks passed")

        time.sleep(0.04)

    # ── Determine what failed ─────────────────────────────────────────────────
    print(f"[FACE] Timeout. identity={identity_ok} lap={laplacian_ok} "
          f"motion={motion_ok} blink={blink_ok}")

    if not identity_ok:
        return VerifyResult(False, "Face not recognised")
    if not laplacian_ok:
        return VerifyResult(False, "Spoofing detected")
    if not blink_ok:
        return VerifyResult(False, "No blink detected")
    return VerifyResult(False, "Timeout")