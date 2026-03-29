"""Utility helpers for paths, naming, and logging."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

from config import CHARTS_DIR, LOGS_DIR, NETS_DIR, TABLES_DIR


def ensure_directories() -> None:
    """Create required output directories if they do not already exist."""
    for directory in (NETS_DIR, CHARTS_DIR, TABLES_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def sanitize_name(name: str) -> str:
    """Return a deterministic filename-safe version of a string."""
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in name)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def now_iso() -> str:
    """Return UTC timestamp string for metadata and logs."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def setup_logger(log_file: Path) -> logging.Logger:
    """Configure a logger that writes to both console and a file."""
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def write_text_report(path: Path, lines: Iterable[str]) -> None:
    """Write a deterministic plaintext/markdown report file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as report_file:
        report_file.write("\n".join(lines).rstrip() + "\n")
