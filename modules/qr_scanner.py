"""
modules/qr_scanner.py  �  Reads a single QR code from the camera.
 
Expected QR payload (JSON):
    {"name": "Alice Sharma", "roll_no": "CS2024001", "dept": "Computer Science"}
 
Returns a dict on success, None on timeout or bad format.
"""
import json
import time
from typing import Optional
 
import cv2
from pyzbar.pyzbar import decode as zbar_decode
 
from config import CAMERA_RESOLUTION
from modules.lcd_controller import lcd
 
 
# -- QR data model -------------------------------------------------------------
 
class StudentQR:
    """Parsed, validated QR payload."""
    __slots__ = ("name", "roll_no", "dept")
 
    def __init__(self, name: str, roll_no: str, dept: str):
        self.name    = name.strip()
        self.roll_no = roll_no.strip().upper()
        self.dept    = dept.strip()
 
    def __repr__(self):
        return f"StudentQR(name={self.name!r}, roll_no={self.roll_no!r}, dept={self.dept!r})"
 
    def display_name(self) -> str:
        """Fits on LCD line 2 (16 chars max)."""
        return self.name[:16]
 
 
def _parse_qr_payload(raw: str) -> Optional[StudentQR]:
    """
    Parse raw QR string.  Accepts:
      � JSON   {"name":"...", "roll_no":"...", "dept":"..."}
      � Future formats can be added here without touching main.py
    """
    raw = raw.strip()
    try:
        data = json.loads(raw)
        name    = data.get("name", "").strip()
        roll_no = data.get("roll_no", "").strip()
        dept    = data.get("dept", "").strip()
 
        if not name or not roll_no:
            print(f"[QR] Missing required fields in: {raw}")
            return None
 
        return StudentQR(name=name, roll_no=roll_no, dept=dept or "General")
 
    except json.JSONDecodeError:
        print(f"[QR] Not valid JSON: {raw!r}")
        return None
# -- Main scanner function ------------------------------------------------------
 
def scan_qr(picam2, timeout: float = 30.0) -> Optional[StudentQR]:
    """
    Continuously grab frames from `picam2` until a valid QR is decoded
    or `timeout` seconds pass.
 
    Args:
        picam2:   A started Picamera2 instance (owned by main.py).
        timeout:  Seconds to wait before giving up.
 
    Returns:
        StudentQR if successful, None on timeout or unrecognised format.
    """
    lcd.show("Ready!", "Scan your QR")
    print("[QR] Scanning�")
 
    deadline = time.time() + timeout
    last_warn = 0.0
 
    while time.time() < deadline:
        frame = picam2.capture_array()
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
 
        objects = zbar_decode(bgr)
        for obj in objects:
            raw = obj.data.decode("utf-8", errors="ignore")
            student = _parse_qr_payload(raw)
            if student:
                print(f"[QR] Decoded: {student}")
                return student
            else:
                # QR found but wrong format � warn once per 3 s
                if time.time() - last_warn > 3:
                    lcd.show("Bad QR format", "Use JSON QR")
                    last_warn = time.time()
 
        time.sleep(0.04)   # ~25 fps polling
 
    print("[QR] Timeout � no valid QR found.")
    lcd.show("QR Timeout", "Try again")
    return None
 