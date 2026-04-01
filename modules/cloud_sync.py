"""
modules/cloud_sync.py  —  Push attendance records to the cloud API.

Strategy:
  • push(record)  — try once; on failure write to pending queue
  • flush_pending() — upload everything in pending_sync/ and delete on success
  • A background thread calls flush_pending() every 60 s
"""
import threading
import time
import requests
from requests.exceptions import RequestException

from config import CLOUD_API_BASE_URL, CLOUD_API_KEY, SYNC_TIMEOUT_SECS, SYNC_RETRY_MAX

# Lazy import to avoid circular dependency at module load time
def _logger():
    import modules.attendance_logger as al
    return al


# ── Internal HTTP helper ──────────────────────────────────────────────────────

_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": CLOUD_API_KEY,
}


def _post(endpoint: str, payload: dict) -> bool:
    """
    POST payload to CLOUD_API_BASE_URL/endpoint.
    Returns True on HTTP 2xx, False on any error.
    """
    if not CLOUD_API_BASE_URL:
        print("[SYNC] CLOUD_API_BASE_URL not set — skipping cloud push.")
        return False

    url = f"{CLOUD_API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    for attempt in range(1, SYNC_RETRY_MAX + 1):
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=_HEADERS,
                timeout=SYNC_TIMEOUT_SECS,
            )
            if resp.status_code in (200, 201):
                print(f"[SYNC] Uploaded OK ({resp.status_code})")
                return True
            else:
                print(f"[SYNC] Server error {resp.status_code}: {resp.text[:120]}")
        except RequestException as e:
            print(f"[SYNC] Attempt {attempt}/{SYNC_RETRY_MAX} failed: {e}")
        time.sleep(1)   # brief pause between retries

    return False


# ── Public API ────────────────────────────────────────────────────────────────

def push(record: dict):
    """
    Try to upload one record now.
    If it fails, save to pending queue for later.
    Runs in the calling thread — fast because timeout is short.
    """
    ok = _post("/api/attendance/mark", record)
    if not ok:
        _logger().save_pending(record)
    else:
        # A successful upload means we're online — try clearing the backlog
        threading.Thread(target=flush_pending, daemon=True).start()


def flush_pending():
    """Upload every pending record; delete each file after success."""
    al = _logger()
    pending = al.load_pending()
    if not pending:
        return

    print(f"[SYNC] Flushing {len(pending)} pending record(s)…")
    for (path, record) in pending:
        ok = _post("/api/attendance/mark", record)
        if ok:
            al.delete_pending(path)
        else:
            print(f"[SYNC] Still offline — will retry later.")
            break   # don't hammer the server; next flush cycle will continue


# ── Background flush thread ───────────────────────────────────────────────────

def _background_flush_loop(interval: int = 60):
    while True:
        time.sleep(interval)
        try:
            flush_pending()
        except Exception as e:
            print(f"[SYNC] Background flush error: {e}")


def start_background_sync(interval: int = 60):
    """Call once from main.py to start the periodic flush thread."""
    t = threading.Thread(
        target=_background_flush_loop,
        args=(interval,),
        daemon=True,
        name="cloud-sync",
    )
    t.start()
    print(f"[SYNC] Background sync started (every {interval}s)")