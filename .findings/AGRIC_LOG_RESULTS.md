# Agriculture LOG Results (SRBench)

Results from SRBench runs on **LOG** Agriculture datasets (transformed targets), 
directly comparable to GINN-LP / MTRGINN-LP. Sources: `results_agric_001_log/`, `results_agric_01_log/`.

## Cross-reference: LOG vs raw runs

| What | LOG pipeline (this report) | Original (raw) pipeline |
|------|-----------------------------|---------------------------|
| **Data** | `data/agric_*_*_log/` (e.g. agric_01_consumer_trend_log) | `data/agric_*_*/` (e.g. agric_01_consumer_trend) |
| **Results** | `results_agric_001_log/`, `results_agric_01_log/` | `results_agric_001/`, `results_agric_01/` |
| **Run logs** | `data/agric_01_consumer_trend_log/agric_01_consumer_trend_log_DSR.log` | `data/agric_01_consumer_trend/agric_01_consumer_trend_DSR.log` |

The file **`data/agric_01_consumer_trend/agric_01_consumer_trend_DSR.log`** (no `_log` in path) is from the **raw** run; its results go to `results_agric_01/`, not into this report. This report uses only **LOG** result JSONs under `results_agric_*_log/`. For LOG DSR on 0.1 consumer_trend, the run log (if present) would be `data/agric_01_consumer_trend_log/agric_01_consumer_trend_log_DSR.log`.

## What "symbolic model" and the metrics mean

- **Symbolic model**: The equation string that the algorithm saved (e.g. a real formula or a fallback like `x0`). When a run **times out** or **fails**, the bridge returns `x0` so that the pipeline still writes a result JSON. So `x0` = no usable equation from that run (time limit or error).
- **Why fallback to x0**: DSR and AIFeynman run in a subprocess with a time limit (e.g. 1–8 hours). On the **0.1 sample** (large data), DSR often hits the limit before finding a good program, so the bridge returns `x0`. On the **0.01 sample**, DSR usually finishes and returns a real traversal. AIFeynman often times out or fails on these datasets, so it also returns `x0`.
- **Why fallback (x0) and "real equation" rows look similar in the table**: In this SRBench setup, **DSRRegressor and AIFeynman use a placeholder `predict()` that always returns zeros** (see `experiment/methods/DSRRegressor.py` and `AIFeynman.py`: `return np.zeros(len(X))`). So the reported MAE/MAPE/RMSE are **not** from evaluating the stored equation or `x0` — they are from **predicting 0 for every test point**. So both "found equation" and "x0" runs get the same treatment at evaluation time; the numbers differ only because the test set (and thus the error of predicting 0) differs by dataset/sample size. To get metrics that reflect the actual discovered equation, `predict()` would need to evaluate the symbolic expression.

## Performance metrics (test set)

Y1 = Sustainability_Score, Y2 = Consumer_Trend_Index. Averages over all trials (including fallback runs).

| Model | MAE (Y1) | MAE (Y2) | Avg. MAE | MAPE (Y1) | MAPE (Y2) | Avg. MAPE | RMSE (Y1) | RMSE (Y2) | Avg. RMSE | MSE (Y1) | MSE (Y2) | Avg. MSE |
|-------|----------|----------|----------|-----------|-----------|-----------|------------|------------|-----------|----------|----------|----------|
| AIFeynman AGRIC 0.01 | 0.70 | 0.27 | 0.49 | 0.29 | 0.06 | 0.17 | 0.89 | 0.31 | 0.60 | 0.78 | 0.10 | 0.44 |
| DSR AGRIC 0.01 | 0.70 | 0.27 | 0.49 | 0.29 | 0.06 | 0.17 | 0.89 | 0.31 | 0.60 | 0.78 | 0.10 | 0.44 |
| AIFeynman AGRIC 0.1 | 0.73 | 0.26 | 0.50 | 0.61 | 0.06 | 0.33 | 0.98 | 0.31 | 0.64 | 0.95 | 0.10 | 0.52 |
| DSR AGRIC 0.1 | 0.73 | 0.26 | 0.50 | 0.61 | 0.06 | 0.33 | 0.98 | 0.31 | 0.64 | 0.95 | 0.10 | 0.52 |

## Discovered equations

Per dataset, algorithm, and seed (trial). Fallback runs (e.g. `x0`) are labeled as such; their metrics are still in the table above.

### agric_001_consumer_trend_log — AIFeynman

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`

### agric_001_consumer_trend_log — DSR

- **Seed 860:** `[mul, sin, mul, x1, x13, cos, x10]`
- **Seed 4426:** `[cos, sub, x1, add, mul, x12, x13, x13]`
- **Seed 5390:** `[mul, sub, mul, sin, x13, x1, x12, sin, exp, x15]`
- **Seed 14423:** `[mul, cos, x10, sin, mul, x13, x1]`
- **Seed 15795:** `[mul, sin, exp, x14, sin, mul, x14, x1]`
- **Seed 16850:** `[sin, div, x13, sub, x12, exp, x13]`
- **Seed 21962:** `[sin, mul, sub, x12, x1, mul, x13, x1]`
- **Seed 23654:** `[mul, mul, mul, x12, sin, x1, x13, cos, x13]`
- **Seed 28020:** `[mul, sin, sub, x10, x13, cos, add, x12, x1]`
- **Seed 29910:** `[mul, sin, mul, x14, x1, sin, exp, x14]`

### agric_001_sustainability_log — AIFeynman

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`

### agric_001_sustainability_log — DSR

- **Seed 860:** `[sin, sub, mul, x2, x1, x1]`
- **Seed 4426:** `[sin, mul, x1, sub, x2, div, x2, x2]`
- **Seed 5390:** `[sin, sub, mul, x2, x1, x1]`
- **Seed 14423:** `[sub, sin, x5, x5]`
- **Seed 15795:** `[mul, cos, x3, sin, sub, x2, x1]`
- **Seed 16850:** `[sin, sub, mul, x2, x1, x1]`
- **Seed 21962:** `[mul, sin, x1, cos, exp, exp, x2]`
- **Seed 23654:** `[sin, sub, mul, x2, x1, x1]`
- **Seed 28020:** `[sub, sin, x5, x5]`
- **Seed 29910:** `[mul, mul, sub, sin, mul, x2, x4, cos, x5, x1, cos, x1]`

### agric_01_consumer_trend_log — AIFeynman

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`

### agric_01_consumer_trend_log — DSR

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`

### agric_01_sustainability_log — AIFeynman

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`

### agric_01_sustainability_log — DSR

- **Seed 860:** `(fallback: 'x0')`
- **Seed 4426:** `(fallback: 'x0')`
- **Seed 5390:** `(fallback: 'x0')`
- **Seed 14423:** `(fallback: 'x0')`
- **Seed 15795:** `(fallback: 'x0')`
- **Seed 16850:** `(fallback: 'x0')`
- **Seed 21962:** `(fallback: 'x0')`
- **Seed 23654:** `(fallback: 'x0')`
- **Seed 28020:** `(fallback: 'x0')`
- **Seed 29910:** `(fallback: 'x0')`
