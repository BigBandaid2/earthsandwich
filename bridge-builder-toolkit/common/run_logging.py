"""Per-run log files under a project folder (T007).

Each stage run gets its own timestamped logfile in ``<project>/logs/`` plus
console output, so a project carries an auditable trail of what ran when.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

LOGS_DIR = "logs"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def close_run_loggers(project_dir: str | Path) -> None:
    """Close + detach any run-log file handlers under ``project_dir``.

    Loggers are process-cached and keep their logfiles open; on Windows an open
    file blocks ``rmtree``, so project deletion must release them first.
    """
    root = Path(project_dir).resolve()
    for logger_obj in list(logging.Logger.manager.loggerDict.values()):
        if not isinstance(logger_obj, logging.Logger) or not logger_obj.name.startswith("bridge_builder."):
            continue
        for handler in list(logger_obj.handlers):
            base = getattr(handler, "baseFilename", None)
            if base and root in Path(base).resolve().parents:
                handler.close()
                logger_obj.removeHandler(handler)


def get_run_logger(project_dir: str | Path, stage: str) -> tuple[logging.Logger, Path]:
    """Return a logger writing to ``<project>/logs/<stage>-<ts>.log`` (+ console)."""
    logs_dir = Path(project_dir) / LOGS_DIR
    logs_dir.mkdir(parents=True, exist_ok=True)
    logfile = logs_dir / f"{stage}-{_timestamp()}.log"

    logger = logging.getLogger(f"bridge_builder.{stage}.{logfile.stem}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler = logging.FileHandler(logfile, encoding="utf-8")
        file_handler.setFormatter(fmt)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger, logfile
