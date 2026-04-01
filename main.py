#!/usr/bin/env python3
"""
main.py  �  Attendance System Kiosk entry point.
 
Flow per student:
  Boot ? LCD "Ready / Scan QR" ? QR scanned (JSON) ? LCD "Welcome <name>"
  ? Face scan + 3-layer anti-spoof ? Attendance marked (CSV + cloud)
  ? LCD result ? repeat
"""
import sys
import time
import signal
 
import RPi.GPIO as GPIO
from picamera2 import Picamera2
 
from config import (
    BUZZER_PIN, CAMERA_RESOLUTION, CAMERA_FORMAT
)
from modules.lcd_controller import lcd
from modules.qr_scanner import scan_qr
from modules.face_engine import load_model, verify_face
from modules.attendance_logger import is_already_marked, mark_attendance
from modules.cloud_sync import start_background_sync
 
 
# -- GPIO setup ----------------------------------------------------------------
 
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
 
 
def beep(count: int = 1, on: float = 0.15, off: float = 0.1):
    for _ in range(count):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(on)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(off)
 
 
# -- Camera setup --------------------------------------------------------------
 
def init_camera() -> Picamera2:
    cam = Picamera2()
    cfg = cam.create_preview_configuration(
        main={"size": CAMERA_RESOLUTION, "format": CAMERA_FORMAT}
    )
    cam.configure(cfg)
    cam.start()
    time.sleep(1)   # let sensor warm up
    print("[CAM] Camera started.")
    return cam
 # -- Graceful shutdown ---------------------------------------------------------
 
_cam: Picamera2 = None
 
def _shutdown(sig, frame):
    print("\n[MAIN] Shutting down�")
    lcd.show("Shutting down", "Please wait")
    if _cam:
        try:
            _cam.stop()
        except Exception:
            pass
    GPIO.cleanup()
    lcd.close()
    sys.exit(0)
 
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT,  _shutdown)
 
 
# -- Main loop -----------------------------------------------------------------
 
def main():
    global _cam
 
    # Startup
    lcd.show("Starting up...", "Please wait")
    print("[MAIN] Loading face model�")
    recognizer, label_map = load_model()
 
    if not recognizer:
        lcd.show("No Face Model", "Run train.py!")
        print("[MAIN] No trained model found. Exiting.")
        # Don't exit completely � let admin train the model and restart service
        while True:
            time.sleep(5)
 
    _cam = init_camera()
    start_background_sync(interval=60)
 
    lcd.show("Ready!", "Scan your QR")
    beep(1)
    print("[MAIN] System ready. Entering main loop.")
 
    while True:
        try:
            # -- PHASE 1: QR scan ------------------------------------------
            student = scan_qr(_cam, timeout=60)
            if student is None:
                lcd.show("Ready!", "Scan your QR")
                continue
 
            # -- PHASE 2: Duplicate check ----------------------------------
            if is_already_marked(student.roll_no):
                lcd.show("Already marked!", student.display_name())
                beep(2)
                time.sleep(2)
                lcd.show("Ready!", "Scan your QR")
                continue
 
            # -- PHASE 3: Welcome message ----------------------------------
            lcd.show("Welcome!", student.display_name())
            beep(1)
            print(f"[MAIN] Recognised QR: {student}")
            time.sleep(1)
 
            # -- PHASE 4: Face verification + anti-spoof -------------------
            lcd.show("Scan your face", "Look at camera")
            result = verify_face(_cam, student.roll_no, recognizer, label_map)
 
            # -- PHASE 5: Mark or reject -----------------------------------
            if result.success:
                mark_attendance(student)
                lcd.show("Attendance", "Marked!")
                beep(1)
                print(f"[MAIN] Attendance marked for {student.roll_no}")
                time.sleep(2)
 
            else:
                reason_short = result.reason[:16]
                lcd.show("Rejected!", reason_short)
                beep(3)
                print(f"[MAIN] Rejected: {result.reason}")
                time.sleep(2)
 
        except Exception as e:
            print(f"[MAIN] Unexpected error: {e}")
            lcd.show("System Error", "Restarting...")
            time.sleep(3)
 
        finally:
            lcd.show("Ready!", "Scan your QR")
 
if __name__ == "__main__":
    main()