"""
CRYSTAL / ARMATECH ASSOCIATES
File Lock Helper

Prevents two processes/users from writing to the same file at once.
Uses a simple .lock file with timeout + stale detection.

Usage:
    from app.services.file_lock import FileLock

    with FileLock(path_to_data_file):
        # safe to read/write here
        ...
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from contextlib import contextmanager


# ============================================================
# CONFIG
# ============================================================

DEFAULT_TIMEOUT = 10.0      # seconds to wait for the lock
STALE_AGE       = 60.0      # if lock file older than this, remove it
POLL_INTERVAL   = 0.1       # seconds between retries


# ============================================================
# FILE LOCK
# ============================================================

class FileLock:
    """
    Simple file-based lock using the atomic 'mkd' pattern.
    """

    def __init__(self, target_file, timeout=DEFAULT_TIMEOUT):
        self.target = Path(target_file)
        self.lock_path = self.target.with_suffix(self.target.suffix + ".lock")
        self.timeout = timeout

    def acquire(self):
        """Try to acquire the lock. Returns True on success."""
        start = time.time()

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                # Atomic create — fails if the file already exists
                fd = os.open(
                    str(self.lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.write(fd, str(os.getpid()).encode("ascii"))
                os.close(fd)
                return True
            except FileExistsError:
                # Lock exists — check if it's stale
                try:
                    age = time.time() - self.lock_path.stat().st_mtime
                    if age > STALE_AGE:
                        # Stale lock — remove and try again
                        try:
                            self.lock_path.unlink()
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                # Wait and retry
                if time.time() - start > self.timeout:
                    return False
                time.sleep(POLL_INTERVAL)
            except Exception:
                return False

    def release(self):
        """Remove the lock file."""
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
        except Exception:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    from pathlib import Path

    test_target = Path("test_lock_file.json")

    with FileLock(test_target) as lock:
        print("Lock acquired")
        print("Lock file exists:", lock.lock_path.exists())

    print("Lock released")
    print("Lock file exists:", lock.lock_path.exists())
