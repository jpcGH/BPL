"""Central configuration constants for the benchmarking pipeline."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
NETS_DIR = OUTPUT_DIR / "nets"
CHARTS_DIR = OUTPUT_DIR / "charts"
TABLES_DIR = OUTPUT_DIR / "tables"
LOGS_DIR = OUTPUT_DIR / "logs"

RESULTS_CSV = TABLES_DIR / "results_summary.csv"
RUN_REPORT = LOGS_DIR / "experiment_report.md"

REQUIRED_EVENT_ATTRIBUTES = ["concept:name"]
PREFERRED_TIMESTAMP_KEYS = [
    "time:timestamp",
    "timestamp",
    "event_timestamp",
]

ALGORITHMS = ["alpha", "heuristics", "inductive"]

PM4PY_DEFAULT_VARIANT_NOTE = (
    "PM4Py API variants differ across versions. The pipeline attempts a stable import-first "
    "strategy and falls back to alternate modules where available."
)
