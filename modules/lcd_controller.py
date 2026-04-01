"""
modules/lcd_controller.py  �  All LCD interaction lives here.
The rest of the app calls lcd.show() and never touches RPLCD directly.
"""
import time
import threading
from config import (
    LCD_I2C_ADDRESS, LCD_I2C_PORT,
    LCD_COLS, LCD_ROWS, LCD_I2C_EXPANDER
)
 
try:
    from RPLCD.i2c import CharLCD
    _RPLCD_AVAILABLE = True
except ImportError:
    _RPLCD_AVAILABLE = False
 
class LCDController:
    """Thread-safe 16�2 I2C LCD wrapper."""
 
    def __init__(self):
        self._lcd = None
        self._lock = threading.Lock()
        self._connect()
 
    # -- Private --------------------------------------------------------------
 
    def _connect(self):
        if not _RPLCD_AVAILABLE:
            print("[LCD] RPLCD not installed � display disabled.")
            return
        try:
            self._lcd = CharLCD(
                i2c_expander=LCD_I2C_EXPANDER,
                address=LCD_I2C_ADDRESS,
                port=LCD_I2C_PORT,
                cols=LCD_COLS,
                rows=LCD_ROWS,
                auto_linebreaks=False,
            )
            self._lcd.clear()
            print("[LCD] Connected at address 0x{:02X}".format(LCD_I2C_ADDRESS))
        except Exception as e:
            print(f"[LCD] Connection failed: {e}")
            self._lcd = None
 
    def _write(self, line1: str, line2: str):
        """Low-level write � caller must hold self._lock."""
        if not self._lcd:
            return
        try:
            self._lcd.clear()
            self._lcd.write_string(line1[:LCD_COLS])
            self._lcd.cursor_pos = (1, 0)
            self._lcd.write_string(line2[:LCD_COLS])
        except Exception as e:
            print(f"[LCD] Write error: {e}")
    # -- Public API ------------------------------------------------------------
 
    def show(self, line1: str, line2: str = ""):
        """
        Display up to two lines.  Truncates silently to 16 chars.
        Safe to call from any thread.
        """
        print(f"[LCD] {line1!r:<16} | {line2!r:<16}")
        with self._lock:
            self._write(str(line1), str(line2))
 
    def scroll_line2(self, message: str, delay: float = 0.35):
        """
        Scroll a long message across line 2 while line 1 stays fixed.
        Runs in the calling thread (blocks until done).
        """
        if len(message) <= LCD_COLS:
            self.show(self._current_line1, message)
            return
        padded = message + "  "
        for i in range(len(padded) - LCD_COLS + 1):
            with self._lock:
                if self._lcd:
                    try:
                        self._lcd.cursor_pos = (1, 0)
                        self._lcd.write_string(padded[i:i + LCD_COLS])
                    except Exception:
                        pass
            time.sleep(delay)
 
    def clear(self):
        with self._lock:
            if self._lcd:
                try:
                    self._lcd.clear()
                except Exception:
                    pass
 
    def close(self):
        with self._lock:
            if self._lcd:
                try:
                    self._lcd.close(clear=True)
                except Exception:
                    pass
 
    # Keep track of line 1 for scroll helper
    _current_line1 = ""
 
    def show_with_scroll(self, line1: str, long_line2: str, delay: float = 0.35):
        """Show line1 fixed, scroll line2 if it's too long."""
        self._current_line1 = str(line1)[:LCD_COLS]
        with self._lock:
            self._write(self._current_line1, "")
        self.scroll_line2(long_line2, delay)
 
 
# -- Module-level singleton � import and use directly -------------------------
lcd = LCDController()
 