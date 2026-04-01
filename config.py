"""
config.py  �  Single source of truth for all settings.
Edit this file (or the .env) to change behaviour. Nothing else needs touching.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
 
# -- Load .env file ----------------------------------------------------------
BASE_DIR = Path("/home/pi/attendance_system")
load_dotenv(BASE_DIR / ".env")
 
# -- LCD ----------------------------------------------------------------------
LCD_I2C_ADDRESS  = 0x27   # confirmed by i2cdetect -y 1
LCD_I2C_PORT     = 1
LCD_COLS         = 16
LCD_ROWS         = 2
LCD_I2C_EXPANDER = "PCF8574"
 
# -- GPIO ---------------------------------------------------------------------
BUZZER_PIN = 18   # BCM numbering
 
# -- Camera -------------------------------------------------------------------
CAMERA_RESOLUTION  = (640, 480)
CAMERA_FORMAT      = "XBGR8888"
 
# -- Face Recognition ---------------------------------------------------------
# Lower  = stricter (fewer false accepts, more false rejects)
# Higher = looser  (more false accepts)
# 60 is a good starting point; retrain and lower to 50 if a stranger slips through.
CONFIDENCE_THRESHOLD = 60
 
# How many seconds to wait for a face before giving up
FACE_TIMEOUT_SECONDS = 15
 
# Anti-spoofing: Laplacian variance below this ? probably a flat photo
LIVENESS_LAPLACIAN_THRESHOLD = 80.0
 
# Anti-spoofing: minimum face-pixel movement between frames ? proves it's live
LIVENESS_MOTION_THRESHOLD = 5.0
 
# -- Paths ---------------------------------------------------------------------
DATA_DIR         = BASE_DIR / "data"
MODEL_PATH       = DATA_DIR / "models" / "face_model.yml"
LABELS_PATH      = DATA_DIR / "models" / "labels.csv"
LOG_DIR          = DATA_DIR / "logs"
PENDING_SYNC_DIR = DATA_DIR / "pending_sync"
 
# Create dirs if they don't exist yet
for _d in [DATA_DIR, MODEL_PATH.parent, LOG_DIR, PENDING_SYNC_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# -- Cloud API -----------------------------------------------------------------
# Fill these in your .env file � never hard-code secrets here.
CLOUD_API_BASE_URL = os.getenv("CLOUD_API_BASE_URL", "")   # e.g. https://your-app.onrender.com
CLOUD_API_KEY      = os.getenv("CLOUD_API_KEY", "")        # shared secret between Pi and backend
SYNC_TIMEOUT_SECS  = 8    # seconds before giving up on a cloud call
SYNC_RETRY_MAX     = 3    # how many times to retry before writing to pending queue
 