# Agriculture LOG datasets (transformed targets)

## Two pipelines (both kept)

| Script | Targets | Use case |
|--------|---------|----------|
| **csv_to_tsvgz_agric.py** | Raw (original scale) | SRBench default; metrics in original scale. |
| **csv_to_tsvgz_agric_log.py** | Transformed (same as codes/Agriculture) | Fair comparison with GINN-LP and MTRGINN-LP; metrics in same space. |

## Creating the LOG datasets

From `srbench/data/`:

```bash
# 0.01 sample → agric_001_sustainability_log, agric_001_consumer_trend_log
python csv_to_tsvgz_agric_log.py 0.01

# 0.1 sample → agric_01_sustainability_log, agric_01_consumer_trend_log
python csv_to_tsvgz_agric_log.py 0.1
```

## Running SRBench on LOG datasets

Use the run scripts in **`srbench/.run_log/`** (log versions live there; main runs stay in `srbench/.run/`):

- `run_dsr_agric_001_log.sh`, `run_dsr_agric_01_log.sh`
- `run_bsr_agric_001_log.sh`, `run_bsr_agric_01_log.sh`
- `run_aifeynman_agric_001_log.sh`, `run_aifeynman_agric_01_log.sh`

Run from repo root, e.g. `bash srbench/.run_log/run_dsr_agric_001_log.sh`.

Results go to `srbench/results_agric_001_log/` and `srbench/results_agric_01_log/`. Metrics from these runs are directly comparable to GINN-LP and MTRGINN-LP Agriculture metrics.

## Preparing and formatting results (this machine)

If you run the LOG experiments on **another station**, copy the result directories here so you can commit and format them:

1. **Copy the result directories** from the other station into `srbench/`:
   - `results_agric_001_log/` (contains subdirs per dataset, each with `*.json` result files)
   - `results_agric_01_log/`

2. **JSON files are tracked:** `.gitignore` is set so that only these two result directories (and their `*.json` files) are **not** ignored. You can commit the copied results.

3. **Format the outputs** (metrics table + discovered equations) into a single report:
   ```bash
   cd srbench
   python format_agric_log_results.py
   ```
   This reads all JSON files under `results_agric_001_log/` and `results_agric_01_log/`, aggregates metrics (MAE, MAPE, RMSE, MSE) per dataset and algorithm (DSR, BSR, AIFeynman), lists the discovered equations per run, and writes:
   - **Output:** `srbench/.findings/AGRIC_LOG_RESULTS.md`

   To use custom result paths or output file:
   ```bash
   python format_agric_log_results.py --results-dir /path/to/results_agric_001_log --results-dir /path/to/results_agric_01_log -o .findings/AGRIC_LOG_RESULTS.md
   ```

The report follows the same style as `.findings/Report_DSR.md` (metrics table with Y1 = Sustainability_Score, Y2 = Consumer_Trend_Index; plus a section listing the symbolic equations found in each run).
