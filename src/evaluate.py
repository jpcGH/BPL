"""Model quality evaluation utilities."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MetricValue:
    """Stores one metric value with optional failure reason."""

    value: Optional[float]
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    """Holds all requested quality metrics."""

    fitness: MetricValue
    precision: MetricValue
    generalization: MetricValue
    simplicity: MetricValue


@dataclass
class MetricRuntime:
    """Stores runtime diagnostics for one metric evaluation."""

    metric: str
    runtime_seconds: float


@dataclass
class EvaluationDiagnostics:
    """Optional diagnostics describing how evaluation was executed."""

    original_trace_count: Optional[int] = None
    evaluated_trace_count: Optional[int] = None
    sampled: bool = False
    metric_runtimes: Optional[list[MetricRuntime]] = None


def _safe_metric(metric_name: str, fn) -> MetricValue:
    try:
        value = fn()
        if isinstance(value, dict):
            if "averageFitness" in value:
                value = value["averageFitness"]
            elif "fitness" in value:
                value = value["fitness"]
        return MetricValue(value=float(value), error=None)
    except Exception as exc:
        return MetricValue(value=None, error=f"{metric_name} failed: {exc}")


def _trace_count(log: object) -> Optional[int]:
    try:
        return len(log)
    except Exception:
        return None


def _sample_log(log: object, max_traces: Optional[int], seed: int = 42) -> tuple[object, Optional[int], Optional[int], bool]:
    original_count = _trace_count(log)
    if max_traces is None or original_count is None or original_count <= max_traces:
        return log, original_count, original_count, False

    indices = sorted(random.Random(seed).sample(range(original_count), max_traces))
    sampled_traces = [log[idx] for idx in indices]

    try:
        from pm4py.objects.log.obj import EventLog

        sampled_log = EventLog(sampled_traces, attributes=getattr(log, "attributes", None))
        return sampled_log, original_count, len(sampled_log), True
    except Exception:
        return sampled_traces, original_count, len(sampled_traces), True


def _timed_metric(metric_name: str, fn) -> tuple[MetricValue, MetricRuntime]:
    start = time.perf_counter()
    metric = _safe_metric(metric_name, fn)
    end = time.perf_counter()
    return metric, MetricRuntime(metric=metric_name, runtime_seconds=end - start)


def evaluate_model(
    log: object,
    net: object,
    initial_marking: object,
    final_marking: object,
    max_traces: Optional[int] = None,
) -> tuple[EvaluationResult, EvaluationDiagnostics]:
    """Evaluate discovered model with PM4Py conformance and quality metrics."""
    from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
    from pm4py.algo.evaluation.replay_fitness import algorithm as fitness_evaluator
    from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator
    from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator

    eval_log, original_count, eval_count, sampled = _sample_log(log, max_traces=max_traces)

    fitness, fitness_runtime = _timed_metric(
        "fitness",
        lambda: fitness_evaluator.apply(eval_log, net, initial_marking, final_marking),
    )
    precision, precision_runtime = _timed_metric(
        "precision",
        lambda: precision_evaluator.apply(eval_log, net, initial_marking, final_marking),
    )
    generalization, generalization_runtime = _timed_metric(
        "generalization",
        lambda: generalization_evaluator.apply(eval_log, net, initial_marking, final_marking),
    )
    simplicity, simplicity_runtime = _timed_metric(
        "simplicity",
        lambda: simplicity_evaluator.apply(net),
    )

    return (
        EvaluationResult(
            fitness=fitness,
            precision=precision,
            generalization=generalization,
            simplicity=simplicity,
        ),
        EvaluationDiagnostics(
            original_trace_count=original_count,
            evaluated_trace_count=eval_count,
            sampled=sampled,
            metric_runtimes=[
                fitness_runtime,
                precision_runtime,
                generalization_runtime,
                simplicity_runtime,
            ],
        ),
    )


def net_statistics(net: object) -> Dict[str, int]:
    """Compute structural Petri net statistics."""
    return {
        "num_places": len(getattr(net, "places", [])),
        "num_transitions": len(getattr(net, "transitions", [])),
        "num_arcs": len(getattr(net, "arcs", [])),
    }
