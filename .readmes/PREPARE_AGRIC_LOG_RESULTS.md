# Preparing Agriculture LOG results on this machine

This machine does **not** run the SRBench LOG experiments (DSR, BSR, AIFeynman on Agriculture LOG). Those run on **another station**. Here we only **receive the result directories**, **keep them in git**, and **format** them for reporting.

## What to do

1. **Copy result directories** from the other station into `srbench/`:
   - `results_agric_001_log/`
   - `results_agric_01_log/`
   Each directory contains one subdirectory per dataset (e.g. `agric_001_sustainability_log/`, `agric_001_consumer_trend_log/`), and each of those contains JSON files like `agric_001_sustainability_log_tuned.DSRRegressor_0.json` with metrics and the discovered equation (`symbolic_model`).

2. **Commit the results:** JSON files under these two directories are **not** ignored (see `.gitignore`). You can add and commit them so the results are in the repo.

3. **Format the outputs:** From `srbench/` run:
   ```bash
   python format_agric_log_results.py
   ```
   This produces `srbench/.findings/AGRIC_LOG_RESULTS.md` with:
   - A **metrics table** (MAE, MAPE, RMSE, MSE for Y1 = Sustainability_Score and Y2 = Consumer_Trend_Index, per algorithm and sample size).
   - A **discovered equations** section listing the symbolic model from each run (dataset, algorithm, seed).

Details (building LOG data, run scripts, comparison with GINN-LP) are in `srbench/data/README_AGRIC_LOG.md` and `srbench/.readmes/AGRIC_LOG_STRATEGY.md`.
