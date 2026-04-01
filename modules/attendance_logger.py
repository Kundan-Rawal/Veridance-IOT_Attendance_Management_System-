"""
modules/attendance_logger.py  —  Local CSV logging + cloud sync queue.

Write path:
  1. Always write to local CSV first (never loses data).
  2. Try to POST to cloud API immediately.
  3. If cloud unreachable → save record to pending_sync/ folder.
  4. On each successful cloud call → flush pending_sync/ records.
"""
import csv
import json
import datetime
from pathlib import Path

from config import LOG_DIR, PENDING_SYNC_DIR
from modules.qr_scanner import StudentQR
import modules.cloud_sync as cloud_sync   # lazy import avoids circular


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _today_csv() -> Path:
    return LOG_DIR / f"attendance_{datetime.date.today().isoformat()}.csv"


def _ensure_header(path: Path):
    if not path.exists():
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(
                ["roll_no", "name", "dept", "date", "time", "status"]
            )


def is_already_marked(roll_no: str) -> bool:
    """Return True if this student already has an entry in today's CSV."""
    path = _today_csv()
    if not path.exists():
        return False
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("roll_no", "").upper() == roll_no.upper():
                    return True
    except Exception as e:
        print(f"[LOG] CSV read error: {e}")
    return False


def mark_attendance(student: StudentQR, status: str = "PRESENT") -> dict:
    """
    Write one attendance record locally and attempt cloud sync.

    Returns the record dict (useful for the cloud payload).
    """
    now = datetime.datetime.now()
    record = {
        "roll_no": student.roll_no,
        "name":    student.name,
        "dept":    student.dept,
        "date":    now.date().isoformat(),
        "time":    now.strftime("%H:%M:%S"),
        "status":  status,
    }

    # ── 1. Local CSV ──────────────────────────────────────────────────────────
    path = _today_csv()
    _ensure_header(path)
    try:
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["roll_no", "name", "dept", "date", "time", "status"]
            )
            writer.writerow(record)
        print(f"[LOG] Written to CSV: {record}")
    except Exception as e:
        print(f"[LOG] CSV write error: {e}")

    # ── 2. Cloud sync (non-blocking attempt) ──────────────────────────────────
    cloud_sync.push(record)

    return record


# ── Pending queue flusher (called by cloud_sync after a successful upload) ───

def save_pending(record: dict):
    """Save a record to pending_sync/ when cloud is unreachable."""
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = PENDING_SYNC_DIR / f"pending_{ts}.json"
    try:
        path.write_text(json.dumps(record))
        print(f"[LOG] Queued for later sync: {path.name}")
    except Exception as e:
        print(f"[LOG] Could not save pending record: {e}")


def load_pending() -> list[dict]:
    """Return all pending records sorted by filename (= creation time)."""
    records = []
    for f in sorted(PENDING_SYNC_DIR.glob("pending_*.json")):
        try:
            records.append((f, json.loads(f.read_text())))
        except Exception:
            pass
    return records


def delete_pending(path: Path):
    try:
        path.unlink(missing_ok=True)
    except Exception as e:
        print(f"[LOG] Could not delete pending file {path}: {e}")