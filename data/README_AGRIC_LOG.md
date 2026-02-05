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
