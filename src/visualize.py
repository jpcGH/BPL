"""Visualization and export helpers for nets and charts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd


def save_petri_net_image(
    net: object,
    initial_marking: object,
    final_marking: object,
    output_path: Path,
) -> None:
    """Save a Petri net rendering using PM4Py's Graphviz visualizer."""
    from pm4py.visualization.petri_net import visualizer as pn_visualizer

    gviz = pn_visualizer.apply(net, initial_marking, final_marking)
    pn_visualizer.save(gviz, str(output_path))


def save_runtime_chart(results_df: pd.DataFrame, output_path: Path) -> None:
    """Create runtime comparison chart by dataset and algorithm."""
    pivot = results_df.pivot(index="dataset", columns="algorithm", values="runtime_seconds")
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Runtime Comparison by Discovery Algorithm")
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Runtime (seconds)")
    ax.legend(title="Algorithm")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_metric_chart(results_df: pd.DataFrame, output_path: Path, metrics: Iterable[str]) -> None:
    """Create grouped metric chart using average metric value by algorithm."""
    metric_rows = []
    for metric in metrics:
        grouped = results_df.groupby("algorithm", dropna=False)[metric].mean(numeric_only=True)
        for algorithm, value in grouped.items():
            metric_rows.append({"algorithm": algorithm, "metric": metric, "value": value})

    metrics_df = pd.DataFrame(metric_rows)
    pivot = metrics_df.pivot(index="algorithm", columns="metric", values="value")

    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Average Metric Comparison by Discovery Algorithm")
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()
