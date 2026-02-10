#!/usr/bin/env python3
"""
Format SRBench Agriculture LOG results for reporting.

Reads JSON result files from results_agric_001_log/ and results_agric_01_log/
(as produced by .run_log scripts on another station), then:
  - Aggregates metrics (MAE, MAPE, RMSE, MSE) per dataset and algorithm
  - Lists discovered equations (symbolic_model) per run
  - Writes a Markdown report in the same style as .findings/Report_DSR.md

Usage:
  From srbench/:  python format_agric_log_results.py
  Or:             python format_agric_log_results.py --results-dir /path/to/results_agric_001_log --results-dir /path/to/results_agric_01_log
  Output:         By default writes to srbench/.findings/AGRIC_LOG_RESULTS.md
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


# Target mapping for display (Y1 = sustainability, Y2 = consumer_trend)
TARGET_LABELS = {
    "sustainability": "Sustainability_Score (Y1)",
    "consumer_trend": "Consumer_Trend_Index (Y2)",
}

# Fallback model strings to exclude from metrics (e.g. timeout fallback)
FALLBACK_MODELS = ("x0", "0", "nan")


def is_fallback(symbolic_model: str | None) -> bool:
    if not symbolic_model or not isinstance(symbolic_model, str):
        return True
    s = symbolic_model.strip()
    return s in FALLBACK_MODELS or not s


def algorithm_display_name(est_name: str) -> str:
    """e.g. tuned.DSRRegressor -> DSR"""
    name = est_name.replace("tuned.", "")
    if "DSR" in name:
        return "DSR"
    if "BSR" in name:
        return "BSR"
    if "AIFeynman" in name:
        return "AIFeynman"
    return name


def collect_jsons(results_dirs: list[Path]) -> list[tuple[Path, str, str, str]]:
    """Yield (path, dataset_name, algorithm, seed) for each JSON."""
    for d in results_dirs:
        if not d.is_dir():
            continue
        for sub in d.iterdir():
            if not sub.is_dir():
                continue
            dataset_name = sub.name
            for f in sub.glob("*.json"):
                # filename: {dataset_name}_{est_name}_{seed}.json
                stem = f.stem
                if not stem.startswith(dataset_name + "_"):
                    continue
                rest = stem[len(dataset_name) + 1 :]
                parts = rest.rsplit("_", 1)
                if len(parts) != 2:
                    continue
                est_name, seed = parts
                yield (f, dataset_name, est_name, seed)


def load_result(path: Path) -> dict | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def aggregate_metrics(rows: list[dict]) -> dict:
    """Compute mean MAE, MAPE, RMSE, MSE (test) over rows. None if no valid."""
    out = {}
    for key in ("mae_test", "mape_test", "rmse_test", "mse_test"):
        vals = [r.get(key) for r in rows if r.get(key) is not None]
        if vals:
            out[key] = sum(vals) / len(vals)
        else:
            out[key] = None
    return out


def build_tables_and_equations(
    results_dirs: list[Path],
) -> tuple[dict, dict, list[tuple[str, str, str, str]]]:
    """
    Returns:
      metrics_by_key: (sample, algo) -> { mae_test, mape_test, rmse_test, mse_test } for Y1 and Y2
      We'll structure as: for each (sample, algo) we have two targets: sustainability (Y1), consumer_trend (Y2).
      So we need: (sample, algo, target) -> list of run dicts, then we aggregate per (sample, algo) for table.
    """
    # (sample, algo, target) -> list of run dicts (with mae_test, symbolic_model, etc.)
    by_group: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    # equations: (dataset_name, algo_display, seed, equation_str)
    equations: list[tuple[str, str, str, str]] = []

    for path, dataset_name, est_name, seed in collect_jsons(results_dirs):
        data = load_result(path)
        if not data:
            continue

        # e.g. agric_001_sustainability_log -> sample=001, target=sustainability
        if "_sustainability_log" in dataset_name:
            target = "sustainability"
        elif "_consumer_trend_log" in dataset_name:
            target = "consumer_trend"
        else:
            continue

        if "agric_001_" in dataset_name:
            sample = "0.01"
        elif "agric_01_" in dataset_name:
            sample = "0.1"
        else:
            sample = "?"

        algo_display = algorithm_display_name(est_name)
        key = (sample, algo_display, target)
        by_group[key].append(data)
        eq = data.get("symbolic_model") or ""
        equations.append((dataset_name, algo_display, seed, eq))

    # Build metrics table from ALL runs (including fallback "x0"). Metrics in the JSON are
    # always computed by evaluating whatever model was saved (real equation or fallback),
    # so e.g. MAPE 0.05 with symbolic_model "x0" is the real test performance of that run.
    metrics_table: dict[tuple[str, str], dict[str, float | None]] = {}
    for (sample, algo, target), runs in by_group.items():
        agg = aggregate_metrics(runs) if runs else {k: None for k in ("mae_test", "mape_test", "rmse_test", "mse_test")}
        row_key = (sample, algo)
        if row_key not in metrics_table:
            metrics_table[row_key] = {}
        suffix = "_Y1" if target == "sustainability" else "_Y2"
        for k, v in agg.items():
            metrics_table[row_key][k + suffix] = v

    # Fill missing keys and averages
    for row_key in metrics_table:
        r = metrics_table[row_key]
        mae1, mae2 = r.get("mae_test_Y1"), r.get("mae_test_Y2")
        r["mae_avg"] = (mae1 + mae2) / 2 if mae1 is not None and mae2 is not None else None
        mape1, mape2 = r.get("mape_test_Y1"), r.get("mape_test_Y2")
        r["mape_avg"] = (mape1 + mape2) / 2 if mape1 is not None and mape2 is not None else None
        rmse1, rmse2 = r.get("rmse_test_Y1"), r.get("rmse_test_Y2")
        r["rmse_avg"] = (rmse1 + rmse2) / 2 if rmse1 is not None and rmse2 is not None else None
        mse1, mse2 = r.get("mse_test_Y1"), r.get("mse_test_Y2")
        r["mse_avg"] = (mse1 + mse2) / 2 if mse1 is not None and mse2 is not None else None

    return metrics_table, by_group, equations


def format_metric(v: float | None) -> str:
    if v is None:
        return "N/A"
    return f"{v:.2f}"


def write_markdown_report(
    metrics_table: dict,
    by_group: dict,
    equations: list,
    out_path: Path,
) -> None:
    """Write .findings-style Markdown report."""
    lines = []
    lines.append("# Agriculture LOG Results (SRBench)")

    lines.append("")
    lines.append("Results from SRBench runs on **LOG** Agriculture datasets (transformed targets), ")
    lines.append("directly comparable to GINN-LP / MTRGINN-LP. Sources: `results_agric_001_log/`, `results_agric_01_log/`.")
    lines.append("")
    lines.append("## Cross-reference: LOG vs raw runs")
    lines.append("")
    lines.append("| What | LOG pipeline (this report) | Original (raw) pipeline |")
    lines.append("|------|-----------------------------|---------------------------|")
    lines.append("| **Data** | `data/agric_*_*_log/` (e.g. agric_01_consumer_trend_log) | `data/agric_*_*/` (e.g. agric_01_consumer_trend) |")
    lines.append("| **Results** | `results_agric_001_log/`, `results_agric_01_log/` | `results_agric_001/`, `results_agric_01/` |")
    lines.append("| **Run logs** | `data/agric_01_consumer_trend_log/agric_01_consumer_trend_log_DSR.log` | `data/agric_01_consumer_trend/agric_01_consumer_trend_DSR.log` |")
    lines.append("")
    lines.append("The file **`data/agric_01_consumer_trend/agric_01_consumer_trend_DSR.log`** (no `_log` in path) is from the **raw** run; its results go to `results_agric_01/`, not into this report. This report uses only **LOG** result JSONs under `results_agric_*_log/`. For LOG DSR on 0.1 consumer_trend, the run log (if present) would be `data/agric_01_consumer_trend_log/agric_01_consumer_trend_log_DSR.log`.")
    lines.append("")

    # Table: rows = (sample, algo), columns = MAE Y1, MAE Y2, Avg MAE, MAPE Y1, MAPE Y2, Avg MAPE, RMSE Y1, RMSE Y2, Avg RMSE, MSE Y1, MSE Y2, Avg MSE
    lines.append("## What \"symbolic model\" and the metrics mean")
    lines.append("")
    lines.append("- **Symbolic model**: The equation string that the algorithm saved (e.g. a real formula or a fallback like `x0`). When a run **times out** or **fails**, the bridge returns `x0` so that the pipeline still writes a result JSON. So `x0` = no usable equation from that run (time limit or error).")
    lines.append("- **Why fallback to x0**: DSR and AIFeynman run in a subprocess with a time limit (e.g. 1–8 hours). On the **0.1 sample** (large data), DSR often hits the limit before finding a good program, so the bridge returns `x0`. On the **0.01 sample**, DSR usually finishes and returns a real traversal. AIFeynman often times out or fails on these datasets, so it also returns `x0`.")
    lines.append("- **Why fallback (x0) and \"real equation\" rows look similar in the table**: In this SRBench setup, **DSRRegressor and AIFeynman use a placeholder `predict()` that always returns zeros** (see `experiment/methods/DSRRegressor.py` and `AIFeynman.py`: `return np.zeros(len(X))`). So the reported MAE/MAPE/RMSE are **not** from evaluating the stored equation or `x0` — they are from **predicting 0 for every test point**. So both \"found equation\" and \"x0\" runs get the same treatment at evaluation time; the numbers differ only because the test set (and thus the error of predicting 0) differs by dataset/sample size. To get metrics that reflect the actual discovered equation, `predict()` would need to evaluate the symbolic expression.")
    lines.append("")
    lines.append("## Performance metrics (test set)")
    lines.append("")
    lines.append("Y1 = Sustainability_Score, Y2 = Consumer_Trend_Index. Averages over all trials (including fallback runs).")
    lines.append("")
    lines.append("| Model | MAE (Y1) | MAE (Y2) | Avg. MAE | MAPE (Y1) | MAPE (Y2) | Avg. MAPE | RMSE (Y1) | RMSE (Y2) | Avg. RMSE | MSE (Y1) | MSE (Y2) | Avg. MSE |")
    lines.append("|-------|----------|----------|----------|-----------|-----------|-----------|------------|------------|-----------|----------|----------|----------|")

    # Deterministic row order: by sample then algo
    row_keys = sorted(metrics_table.keys(), key=lambda x: (x[0], x[1]))
    for (sample, algo) in row_keys:
        r = metrics_table[(sample, algo)]
        label = f"{algo} AGRIC {sample}"
        line = (
            f"| {label} | "
            f"{format_metric(r.get('mae_test_Y1'))} | {format_metric(r.get('mae_test_Y2'))} | {format_metric(r.get('mae_avg'))} | "
            f"{format_metric(r.get('mape_test_Y1'))} | {format_metric(r.get('mape_test_Y2'))} | {format_metric(r.get('mape_avg'))} | "
            f"{format_metric(r.get('rmse_test_Y1'))} | {format_metric(r.get('rmse_test_Y2'))} | {format_metric(r.get('rmse_avg'))} | "
            f"{format_metric(r.get('mse_test_Y1'))} | {format_metric(r.get('mse_test_Y2'))} | {format_metric(r.get('mse_avg'))} |"
        )
        lines.append(line)

    lines.append("")
    lines.append("## Discovered equations")
    lines.append("")
    lines.append("Per dataset, algorithm, and seed (trial). Fallback runs (e.g. `x0`) are labeled as such; their metrics are still in the table above.")
    lines.append("")

    # Group equations by (dataset, algo); show actual stored value (e.g. x0) for fallbacks
    eq_by_da: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for dataset_name, algo_display, seed, eq in equations:
        if is_fallback(eq):
            eq = f"(fallback: {eq!r})" if eq and eq.strip() else "(fallback or empty)"
        eq_by_da[(dataset_name, algo_display)].append((seed, eq))

    for (dataset_name, algo_display) in sorted(eq_by_da.keys()):
        lines.append(f"### {dataset_name} — {algo_display}")
        lines.append("")
        for seed, eq in sorted(eq_by_da[(dataset_name, algo_display)], key=lambda x: (int(x[0]) if x[0].isdigit() else 0, x[0])):
            lines.append(f"- **Seed {seed}:** `{eq}`")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Format Agriculture LOG result JSONs into a Markdown report.")
    parser.add_argument(
        "--results-dir",
        dest="results_dirs",
        action="append",
        type=Path,
        help="Path to a results directory (e.g. results_agric_001_log). Can be repeated.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output Markdown file (default: srbench/.findings/AGRIC_LOG_RESULTS.md)",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    if args.results_dirs:
        results_dirs = [Path(p).resolve() for p in args.results_dirs]
    else:
        results_dirs = [
            base / "results_agric_001_log",
            base / "results_agric_01_log",
        ]

    if args.output is None:
        args.output = base / ".findings" / "AGRIC_LOG_RESULTS.md"
    else:
        args.output = Path(args.output).resolve()

    metrics_table, by_group, equations = build_tables_and_equations(results_dirs)
    write_markdown_report(metrics_table, by_group, equations, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
