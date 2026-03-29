"""CLI entry-point for process discovery benchmarking pipeline.

Run with:
    python src/main.py
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Dict, List

import pandas as pd

from config import (
    ALGORITHMS,
    CHARTS_DIR,
    DATA_DIR,
    EVALUATION_MAX_TRACES,
    EVALUATION_MAX_VARIANTS,
    NETS_DIR,
    PM4PY_DEFAULT_VARIANT_NOTE,
    PREFERRED_TIMESTAMP_KEYS,
    REQUIRED_EVENT_ATTRIBUTES,
    RESULTS_CSV,
    RUN_REPORT,
)
from discover import run_discovery
from evaluate import evaluate_model, net_statistics
from loaders import LogDataset, load_xes_logs
from preprocess import preprocess_log
from utils import ensure_directories, now_iso, sanitize_name, setup_logger, write_text_report
from visualize import save_metric_chart, save_petri_net_image, save_runtime_chart


def _dataset_summary_line(dataset: LogDataset) -> str:
    return (
        f"- {dataset.name}: cases={dataset.num_cases}, events={dataset.num_events}, "
        f"unique_activities={dataset.num_unique_activities}, file={dataset.path.name}"
    )


def run_pipeline(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Run complete benchmark pipeline and return results table."""
    ensure_directories()
    logger = setup_logger(RUN_REPORT.with_suffix(".log"))

    report_lines: List[str] = [
        "# Experiment Report",
        "",
        f"Run timestamp (UTC): {now_iso()}",
        f"Input directory: {data_dir}",
        f"Algorithms: {', '.join(ALGORITHMS)}",
        f"Evaluation max traces per dataset/algorithm: {EVALUATION_MAX_TRACES}",
        f"Evaluation max variants per dataset/algorithm: {EVALUATION_MAX_VARIANTS}",
        f"PM4Py note: {PM4PY_DEFAULT_VARIANT_NOTE}",
        "",
        "## Dataset Summary",
    ]

    datasets = load_xes_logs(data_dir)
    for dataset in datasets:
        line = _dataset_summary_line(dataset)
        logger.info(line.replace("- ", ""))
        report_lines.append(line)

    records: List[Dict[str, object]] = []

    for dataset in datasets:
        logger.info("Starting dataset: %s", dataset.name)
        preprocessed = preprocess_log(
            dataset.log,
            dataset_name=dataset.name,
            required_attributes=REQUIRED_EVENT_ATTRIBUTES,
            timestamp_keys=PREFERRED_TIMESTAMP_KEYS,
        )

        for warning in preprocessed.warnings:
            logger.warning(warning)

        try:
            discovery_outputs = run_discovery(preprocessed.cleaned_log, ALGORITHMS)
        except Exception as exc:
            logger.error("Discovery failed on dataset %s: %s", dataset.name, exc)
            logger.debug(traceback.format_exc())
            report_lines.append(f"- Discovery failed for {dataset.name}: {exc}")
            continue

        for algorithm, discovered in discovery_outputs.items():
            logger.info("Evaluating %s on %s", algorithm, dataset.name)
            evaluation, diagnostics = evaluate_model(
                preprocessed.cleaned_log,
                discovered.net,
                discovered.initial_marking,
                discovered.final_marking,
                max_traces=EVALUATION_MAX_TRACES,
                max_variants=EVALUATION_MAX_VARIANTS,
            )
            if diagnostics.sampled:
                logger.warning(
                    "Evaluation for %s/%s was sampled from %s to %s traces to control runtime.",
                    dataset.name,
                    algorithm,
                    diagnostics.original_trace_count,
                    diagnostics.evaluated_trace_count,
                )
            if diagnostics.metric_runtimes:
                runtime_str = ", ".join(
                    f"{item.metric}={item.runtime_seconds:.2f}s" for item in diagnostics.metric_runtimes
                )
                logger.info("Metric runtimes for %s/%s: %s", dataset.name, algorithm, runtime_str)
            if diagnostics.variant_sampled:
                logger.warning(
                    "Evaluation variants for %s/%s were sampled from %s to %s representatives to improve alignment speed.",
                    dataset.name,
                    algorithm,
                    diagnostics.original_variant_count,
                    diagnostics.evaluated_variant_count,
                )
            stats = net_statistics(discovered.net)

            net_filename = f"{sanitize_name(dataset.name)}__{sanitize_name(algorithm)}.png"
            net_path = NETS_DIR / net_filename
            try:
                save_petri_net_image(
                    discovered.net,
                    discovered.initial_marking,
                    discovered.final_marking,
                    net_path,
                )
            except Exception as exc:
                logger.warning(
                    "Could not save net image for %s/%s: %s",
                    dataset.name,
                    algorithm,
                    exc,
                )

            record = {
                "dataset": dataset.name,
                "algorithm": algorithm,
                "fitness": evaluation.fitness.value,
                "fitness_error": evaluation.fitness.error,
                "precision": evaluation.precision.value,
                "precision_error": evaluation.precision.error,
                "generalization": evaluation.generalization.value,
                "generalization_error": evaluation.generalization.error,
                "simplicity": evaluation.simplicity.value,
                "simplicity_error": evaluation.simplicity.error,
                "runtime_seconds": round(discovered.runtime_seconds, 6),
                "evaluated_traces": diagnostics.evaluated_trace_count,
                "trace_sampling_used": diagnostics.sampled,
                "evaluated_variants": diagnostics.evaluated_variant_count,
                "variant_sampling_used": diagnostics.variant_sampled,
                **stats,
                "net_image": str(net_path),
            }
            records.append(record)

    results_df = pd.DataFrame(records)

    if not results_df.empty:
        RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(RESULTS_CSV, index=False)

        runtime_chart_path = CHARTS_DIR / "runtime_comparison.png"
        metric_chart_path = CHARTS_DIR / "metric_comparison.png"
        save_runtime_chart(results_df, runtime_chart_path)
        save_metric_chart(
            results_df,
            metric_chart_path,
            metrics=["fitness", "precision", "generalization", "simplicity"],
        )

        report_lines.extend(
            [
                "",
                "## Outputs",
                f"- Results table: {RESULTS_CSV}",
                f"- Runtime chart: {runtime_chart_path}",
                f"- Metric chart: {metric_chart_path}",
                "- Petri net images: outputs/nets/*.png",
            ]
        )
    else:
        report_lines.extend(["", "No results produced."])

    write_text_report(RUN_REPORT, report_lines)
    logger.info("Pipeline complete. Rows produced: %d", len(results_df))
    return results_df


if __name__ == "__main__":
    run_pipeline()
