"""Per-project PID lockfile (T006, FR-110).

A project folder holds at most one live operation. The lock is a ``.lock`` file
containing the owner PID; a lock whose PID is no longer alive is *stale* and is
reclaimed automatically, so a crashed run never wedges a project permanently.
"""
from __future__ import annotations

import os
from pathlib import Path

LOCK_FILE = ".lock"


class LockHeldError(RuntimeError):
    """Raised when a project is locked by another *live* process."""


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True            # exists, owned by another user
    return True


class ProjectLock:
    """Acquire/release a per-project lock; usable as a context manager."""

    def __init__(self, project_dir: str | Path) -> None:
        self.path = Path(project_dir) / LOCK_FILE

    def _read_owner(self) -> int | None:
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        try:
            return int(raw)
        except ValueError:
            return None        # corrupt lock — treat as stale

    def acquire(self, *, force: bool = False) -> "ProjectLock":
        owner = self._read_owner()
        if owner is not None and owner != os.getpid() and _pid_alive(owner) and not force:
            raise LockHeldError(f"project is locked by live PID {owner} ({self.path})")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def release(self) -> None:
        if self._read_owner() == os.getpid():
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass

    def __enter__(self) -> "ProjectLock":
        return self.acquire()

    def __exit__(self, *exc: object) -> None:
        self.release()
