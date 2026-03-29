#!/usr/bin/env python3
"""Benchmark XES datasets found under ./data and export summary CSV."""

from __future__ import annotations

import csv
from pathlib import Path
import xml.etree.ElementTree as ET

DATA_DIR = Path("data")
OUTPUT_CSV = Path("outputs/tables/dataset_summary.csv")


def _local_name(tag: str) -> str:
    """Return local XML tag name without namespace."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def summarize_xes_file(xes_path: Path) -> dict[str, int | str]:
    """Compute case/event/activity statistics for a single XES file."""
    case_count = 0
    event_count = 0
    unique_activities: set[str] = set()

    for _event, elem in ET.iterparse(xes_path, events=("end",)):
        name = _local_name(elem.tag)

        if name == "trace":
            case_count += 1
            elem.clear()
            continue

        if name == "event":
            event_count += 1
            for child in elem:
                if _local_name(child.tag) == "string" and child.attrib.get("key") == "concept:name":
                    value = child.attrib.get("value")
                    if value:
                        unique_activities.add(value)
                    break
            elem.clear()

    return {
        "dataset": xes_path.name,
        "num_cases": case_count,
        "num_events": event_count,
        "num_unique_activities": len(unique_activities),
    }


def main() -> None:
    xes_files = sorted(DATA_DIR.glob("*.xes"))

    if not xes_files:
        raise SystemExit(f"No .xes files found in {DATA_DIR.resolve()}")

    summaries = [summarize_xes_file(path) for path in xes_files]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["dataset", "num_cases", "num_events", "num_unique_activities"],
        )
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Processed {len(summaries)} dataset(s). Summary written to {OUTPUT_CSV}")
    for row in summaries:
        print(
            f"- {row['dataset']}: cases={row['num_cases']}, "
            f"events={row['num_events']}, unique_activities={row['num_unique_activities']}"
        )


if __name__ == "__main__":
    main()
