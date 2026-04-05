import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path("/home/pi/attendance_system")
load_dotenv(BASE_DIR / ".env")

# LCD
LCD_I2C_ADDRESS  = 0x27
LCD_I2C_PORT     = 1
LCD_COLS         = 16
LCD_ROWS         = 2
LCD_I2C_EXPANDER = "PCF8574"

# GPIO
BUZZER_PIN = 18

# Camera
CAMERA_RESOLUTION = (640, 480)
CAMERA_FORMAT     = "XBGR8888"

# Face recognition
CONFIDENCE_THRESHOLD = 60

# Timeout
FACE_TIMEOUT_SECONDS = 15

# Anti-spoofing — LOWERED to match real Pi camera output
LIVENESS_LAPLACIAN_THRESHOLD = 40.0   # was 80, real faces score 40-80 on Pi cam
LIVENESS_MOTION_THRESHOLD    = 5.0

# Paths
DATA_DIR         = BASE_DIR / "data"
MODEL_PATH       = DATA_DIR / "models" / "face_model.yml"
LABELS_PATH      = DATA_DIR / "models" / "labels.csv"
LOG_DIR          = DATA_DIR / "logs"
PENDING_SYNC_DIR = DATA_DIR / "pending_sync"

for _d in [DATA_DIR, MODEL_PATH.parent, LOG_DIR, PENDING_SYNC_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# Cloud
CLOUD_API_BASE_URL = os.getenv("CLOUD_API_BASE_URL", "")
CLOUD_API_KEY      = os.getenv("CLOUD_API_KEY", "")
SYNC_TIMEOUT_SECS  = 8
SYNC_RETRY_MAX     = 3

# Haar cascades
HAAR_FACE = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"
HAAR_EYE  = "/usr/share/opencv4/haarcascades/haarcascade_eye.xml"