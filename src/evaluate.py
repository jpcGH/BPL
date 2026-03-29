"""Model quality evaluation utilities."""

from __future__ import annotations

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


def evaluate_model(log: object, net: object, initial_marking: object, final_marking: object) -> EvaluationResult:
    """Evaluate discovered model with PM4Py conformance and quality metrics."""
    from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
    from pm4py.algo.evaluation.replay_fitness import algorithm as fitness_evaluator
    from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator
    from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator

    fitness = _safe_metric(
        "fitness",
        lambda: fitness_evaluator.apply(log, net, initial_marking, final_marking),
    )
    precision = _safe_metric(
        "precision",
        lambda: precision_evaluator.apply(log, net, initial_marking, final_marking),
    )
    generalization = _safe_metric(
        "generalization",
        lambda: generalization_evaluator.apply(log, net, initial_marking, final_marking),
    )
    simplicity = _safe_metric(
        "simplicity",
        lambda: simplicity_evaluator.apply(net),
    )

    return EvaluationResult(
        fitness=fitness,
        precision=precision,
        generalization=generalization,
        simplicity=simplicity,
    )


def net_statistics(net: object) -> Dict[str, int]:
    """Compute structural Petri net statistics."""
    return {
        "num_places": len(getattr(net, "places", [])),
        "num_transitions": len(getattr(net, "transitions", [])),
        "num_arcs": len(getattr(net, "arcs", [])),
    }
