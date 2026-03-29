"""Dataset loading helpers for XES event logs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from pm4py.objects.log.importer.xes import importer as xes_importer


@dataclass
class LogDataset:
    """Container for one loaded dataset and summary metadata."""

    name: str
    path: Path
    log: object
    num_cases: int
    num_events: int
    num_unique_activities: int


def _count_unique_activities(log: object) -> int:
    activities = set()
    for trace in log:
        for event in trace:
            activity = event.get("concept:name")
            if activity is not None:
                activities.add(activity)
    return len(activities)


def load_xes_logs(data_dir: Path) -> List[LogDataset]:
    """Load all .xes logs in a folder and return typed dataset objects."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    xes_paths = sorted(path for path in data_dir.iterdir() if path.suffix.lower() == ".xes")
    if not xes_paths:
        raise FileNotFoundError(f"No .xes files found in: {data_dir}")

    datasets: List[LogDataset] = []
    for path in xes_paths:
        log = xes_importer.apply(str(path))
        num_cases = len(log)
        num_events = sum(len(trace) for trace in log)
        num_unique_activities = _count_unique_activities(log)

        datasets.append(
            LogDataset(
                name=path.stem,
                path=path,
                log=log,
                num_cases=num_cases,
                num_events=num_events,
                num_unique_activities=num_unique_activities,
            )
        )

    return datasets
