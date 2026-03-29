"""Preprocessing routines for PM4Py event logs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class PreprocessResult:
    """Holds cleaned log and preprocessing diagnostics."""

    cleaned_log: object
    warnings: List[str]


def _parse_timestamp(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _find_timestamp_key(event: Dict[str, object], candidate_keys: List[str]) -> Optional[str]:
    for key in candidate_keys:
        if key in event:
            return key
    return None


def _empty_log_like(log: object) -> object:
    """Return an empty log instance while preserving the log's concrete type when possible."""
    cleaned_log = deepcopy(log)

    clear_method = getattr(cleaned_log, "clear", None)
    if callable(clear_method):
        clear_method()
        return cleaned_log

    if hasattr(cleaned_log, "_list"):
        cleaned_log._list = []  # type: ignore[attr-defined]
        return cleaned_log

    try:
        return type(log)()
    except Exception:
        return []


def preprocess_log(
    log: object,
    dataset_name: str,
    required_attributes: List[str],
    timestamp_keys: List[str],
) -> PreprocessResult:
    """
    Validate event attributes, sort traces by timestamp where possible,
    and skip malformed traces.
    """
    warnings: List[str] = []
    cleaned_log = _empty_log_like(log)

    for trace_index, trace in enumerate(log):
        if not trace:
            warnings.append(f"[{dataset_name}] skipped empty trace at index {trace_index}.")
            continue

        malformed = False
        for event_index, event in enumerate(trace):
            missing = [attr for attr in required_attributes if attr not in event]
            if missing:
                warnings.append(
                    f"[{dataset_name}] trace {trace_index} event {event_index} missing attributes: {missing}."
                )
                malformed = True
                break

        if malformed:
            warnings.append(f"[{dataset_name}] skipped malformed trace {trace_index}.")
            continue

        first_event = trace[0]
        timestamp_key = _find_timestamp_key(first_event, timestamp_keys)
        if timestamp_key is None:
            warnings.append(
                f"[{dataset_name}] trace {trace_index} not sorted (no supported timestamp key)."
            )
            cleaned_log.append(trace)
            continue

        parsed_pairs: List[Tuple[datetime, Dict[str, object]]] = []
        unsortable = False
        for event in trace:
            parsed = _parse_timestamp(event.get(timestamp_key))
            if parsed is None:
                unsortable = True
                break
            parsed_pairs.append((parsed, event))

        if unsortable:
            warnings.append(
                f"[{dataset_name}] trace {trace_index} has unparseable timestamp(s); kept original order."
            )
            cleaned_log.append(trace)
        else:
            sorted_events = [event for _, event in sorted(parsed_pairs, key=lambda item: item[0])]
            trace[:] = sorted_events
            cleaned_log.append(trace)
    return PreprocessResult(cleaned_log=cleaned_log, warnings=warnings)
