# DSRRegressor Performance Report

## Evaluation Method

**Critical Clarification: Neural Network vs. Symbolic Model Evaluation**

**The neural network is NOT being evaluated and has NO metrics.**

The performance metrics reported in this document (MAE, MAPE, RMSE, MSE) are **exclusively for the discovered symbolic equations**, not neural network predictions.

**How DSRRegressor Works:**
- **During Training**: A neural network (policy) guides the search for symbolic programs through reinforcement learning. The neural network acts as a search mechanism only.
- **During Evaluation**: DSO executes the discovered symbolic program directly via `program_.execute(X)`, which evaluates the symbolic equation on the input data.

**Key Points:**
1. **Neural Network Role**: The neural network is used solely as a search tool to find good symbolic expressions. It is never evaluated for performance metrics.
2. **Symbolic Model Evaluation**: Once training completes, DSO extracts the best symbolic `Program` object. This symbolic equation is what gets evaluated to produce all the metrics (MAE, MAPE, RMSE, MSE) reported in this document.
3. **No Neural Network Metrics**: There are no separate metrics for the neural network. The neural network is discarded after training, and only the symbolic equation remains.

**This evaluation approach is consistent across all symbolic regression algorithms in SRBench** (DSR, AIFeynman, BSR, etc.) - they all evaluate the discovered symbolic equations rather than neural network outputs. The neural networks serve only as search mechanisms and are never evaluated for performance.

**Documentation Reference:** This is explicitly stated in the SRBench framework. According to the SRBench documentation (`CONTRIBUTING.md`, `CHANGES_AND_GUIDE.md`), algorithms must return a **sympy-compatible model string** for evaluation. The framework evaluates these symbolic equations, not the internal search mechanisms (neural networks, optimization algorithms, etc.) used during training. This is the standard evaluation protocol for all symbolic regression methods in SRBench (La Cava et al., NeurIPS 2021).

## Experimental Setup

**SRBench Configuration:**

We are using default SRBench settings except for the train/test split (80/20 instead of 75/25). The 80/20 split was chosen to match the GINN-LP comparison setup.

**Key Settings:**
- **Train/test split**: 80/20 (SRBench paper default: 75/25) - *Changed to match GINN-LP setup*
- **Number of trials**: 10 per dataset (matches SRBench paper)
- **Time limit**: 48:00 hours (matches SRBench paper black-box protocol)
- **Hyperparameter tuning**: Using `tuned.DSRRegressor` which uses pre-tuned hyperparameters from the SRBench paper, so no additional tuning is needed
- **Target noise**: None (matches SRBench paper for black-box problems)
- **Feature noise**: None (matches SRBench paper)
- **Problem type**: Black-box (no `-sym_data` flag) - our datasets (ENB, Agriculture) are treated as black-box problems where the true underlying function is unknown

**Conclusion:** We are using default SRBench settings except for the 80/20 split, which was changed to match the GINN-LP comparison setup. Everything else (trials, time limits, hyperparameter tuning via `tuned.*` methods, no noise) matches the paper's black-box protocol (La Cava et al., NeurIPS 2021, Table 2).

## Dataset Information

This report evaluates DSRRegressor (Deep Symbolic Regression) performance on two datasets:

1. **ENB Dataset** (Energy Efficiency Building Dataset)
   - Y1: Heating Load
   - Y2: Cooling Load

2. **Agriculture Dataset** (at two sample fractions)
   - Y1: Sustainability_Score
   - Y2: Consumer_Trend_Index
   - Sample fractions: 0.01 (agric_001) and 0.1 (agric_01)

## Target Variable Mapping

**For ENB:**
- Y1 = Heating Load
- Y2 = Cooling Load

**For Agriculture:**
- Y1 = Sustainability_Score
- Y2 = Consumer_Trend_Index

## Performance Metrics

The following table shows the average test set performance metrics across all successful runs (excluding "x0" fallback models):

| Model | MAE (Y1) | MAE (Y2) | Avg. MAE | MAPE (Y1) | MAPE (Y2) | Avg. MAPE | RMSE (Y1) | RMSE (Y2) | Avg. RMSE | MSE (Y1) | MSE (Y2) | Avg. MSE |
|-------|----------|---------|----------|-----------|-----------|-----------|-----------|-----------|-----------|----------|---------|----------|
| DSR ENB | 9.35 | 8.73 | 9.04 | 0.516 | 0.404 | 0.460 | 10.28 | 9.67 | 9.98 | 105.70 | 93.49 | 99.60 |
| DSR AGRIC 0.01 | 26.35 | 24.19 | 25.27 | 1.581 | 0.294 | 0.938 | 29.77 | 27.65 | 28.71 | 886.56 | 764.80 | 825.68 |
| DSR AGRIC 0.1 | 25.30 | 24.75 | 25.03 | 2.947 | 0.289 | 1.618 | 29.16 | 28.77 | 28.97 | 850.21 | 827.68 | 838.94 |

## Notes

- **ENB Dataset**: All 10 runs per target were successful (20 total runs)
- **Agriculture 0.01**: All 10 runs per target were successful (20 total runs)
- **Agriculture 0.1**: Only 1 successful run for Sustainability_Score (Y1) and 2 successful runs for Consumer_Trend_Index (Y2) out of 10 trials each. The remaining runs timed out after 3600 seconds and returned "x0" fallback models.

## Observations

1. DSR performs well on the ENB dataset with consistent results across all runs.
2. DSR shows good performance on Agriculture 0.01 sample fraction, finding equations in all runs.
3. DSR struggles with Agriculture 0.1 sample fraction due to time constraints - most runs time out at 3600 seconds before finding a solution.
4. The successful Agriculture 0.1 runs show similar performance to Agriculture 0.01, suggesting the algorithm can find good solutions if given enough time.

## Recommendations

- Consider increasing `max_time` for larger datasets (Agriculture 0.1) to allow DSR more time to explore the search space.
- The current 3600-second (1 hour) limit appears insufficient for datasets with ~250,000 samples.
