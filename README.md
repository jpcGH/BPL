# Modern Approaches to Petri Net Model Mining on Business Processes

This repository provides a clean and reproducible benchmarking pipeline for MSc dissertation experiments on Petri net process discovery from XES event logs.

## Objectives

The pipeline benchmarks three PM4Py discovery algorithms:
- Alpha Miner
- Heuristic Miner
- Inductive Miner

For each dataset and algorithm, it generates:
- discovered Petri net (with image export)
- fitness, precision, generalization, simplicity
- runtime in seconds
- structural statistics (places, transitions, arcs)

## Project Structure

```text
project_root/
  data/
  outputs/
    nets/
    charts/
    tables/
    logs/
  src/
    config.py
    main.py
    loaders.py
    preprocess.py
    discover.py
    evaluate.py
    visualize.py
    utils.py
  requirements.txt
  README.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place one or more `.xes` files in `./data/`.

## Run

```bash
python src/main.py
```

## Generated Outputs

- `outputs/tables/results_summary.csv`
- `outputs/charts/runtime_comparison.png`
- `outputs/charts/metric_comparison.png`
- `outputs/nets/<dataset>__<algorithm>.png`
- `outputs/logs/experiment_report.md`
- `outputs/logs/experiment_report.log`

## Sample Output Formats

### CSV columns (`results_summary.csv`)

- dataset
- algorithm
- fitness / fitness_error
- precision / precision_error
- generalization / generalization_error
- simplicity / simplicity_error
- runtime_seconds
- num_places
- num_transitions
- num_arcs
- net_image

### Experiment report (`experiment_report.md`)

The report contains:
- run timestamp and algorithm list
- dataset-level summary statistics
- output artifact locations

## Reproducibility Notes

- Deterministic naming is used for all generated files.
- Discovery/evaluation failures are captured per metric to avoid stopping the full benchmark.
- PM4Py API differences across versions are handled with defensive fallbacks in discovery.

## Mapping Outputs to Dissertation Chapter 4

Suggested use in Chapter 4:

1. **Experimental Setup (Section 4.x)**
   - Use `experiment_report.md` for run configuration and dataset overview.

2. **Quantitative Results (Section 4.x)**
   - Use `results_summary.csv` as the source table for metric and runtime comparisons.

3. **Visual Analysis (Section 4.x)**
   - Use `runtime_comparison.png` and `metric_comparison.png` for algorithm-level visual comparison.
   - Use individual net images in `outputs/nets/` for structural/qualitative discussion.

4. **Discussion and Interpretation (Section 4.x)**
   - Use metric error columns and log warnings to document limitations, malformed data handling, and robustness decisions.

## Extending the Benchmark

To add a new discovery algorithm:
1. Add a runner in `src/discover.py`.
2. Register it in `ALGORITHMS` in `src/config.py`.
3. Re-run `python src/main.py`.
