"""Petri net discovery wrappers with runtime tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Tuple


@dataclass
class DiscoveryOutput:
    """Result for one discovery algorithm execution."""

    algorithm: str
    net: object
    initial_marking: object
    final_marking: object
    runtime_seconds: float


def _timed(fn: Callable[[object], Tuple[object, object, object]], log: object) -> Tuple[Tuple[object, object, object], float]:
    start = time.perf_counter()
    output = fn(log)
    end = time.perf_counter()
    return output, end - start


def _discover_alpha(log: object) -> Tuple[object, object, object]:
    from pm4py.algo.discovery.alpha import algorithm as alpha_miner

    return alpha_miner.apply(log)


def _discover_heuristics(log: object) -> Tuple[object, object, object]:
    from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner

    return heuristics_miner.apply(log)


def _discover_inductive(log: object) -> Tuple[object, object, object]:
    try:
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        process_tree = inductive_miner.apply(log)
        from pm4py.objects.conversion.process_tree import converter as tree_converter

        return tree_converter.apply(process_tree)
    except Exception:
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        return inductive_miner.apply(log)


def run_discovery(log: object, algorithms: list[str]) -> Dict[str, DiscoveryOutput]:
    """Run selected discovery algorithms and return outputs keyed by name."""
    runners: Dict[str, Callable[[object], Tuple[object, object, object]]] = {
        "alpha": _discover_alpha,
        "heuristics": _discover_heuristics,
        "inductive": _discover_inductive,
    }

    results: Dict[str, DiscoveryOutput] = {}
    for name in algorithms:
        if name not in runners:
            raise ValueError(f"Unsupported algorithm: {name}")
        output, runtime = _timed(runners[name], log)
        net, initial_marking, final_marking = output
        results[name] = DiscoveryOutput(
            algorithm=name,
            net=net,
            initial_marking=initial_marking,
            final_marking=final_marking,
            runtime_seconds=runtime,
        )
    return results
