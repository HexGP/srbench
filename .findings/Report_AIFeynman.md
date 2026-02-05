# AIFeynman Performance Report

## Evaluation Method

**Critical Clarification: Neural Network vs. Symbolic Model Evaluation**

**The neural network is NOT being evaluated and has NO metrics.**

The performance metrics reported in this document (MAE, MAPE, RMSE, MSE) are **exclusively for the discovered symbolic equations**, not neural network predictions.

**How AIFeynman Works:**
- **During Training**: Neural networks are used during the search/optimization phase to identify patterns and guide the discovery of symbolic expressions. The neural networks act as search mechanisms only.
- **During Evaluation**: The discovered symbolic equation is evaluated directly using SymPy's `lambdify()` function, which converts the symbolic expression into a numerical function for evaluation.

**Key Points:**
1. **Neural Network Role**: The neural networks are used solely as search tools to find good symbolic expressions. They are never evaluated for performance metrics.
2. **Symbolic Model Evaluation**: Once training completes, AIFeynman extracts the best symbolic equation. This symbolic equation is what gets evaluated to produce all the metrics (MAE, MAPE, RMSE, MSE) reported in this document.
3. **No Neural Network Metrics**: There are no separate metrics for the neural networks. The neural networks are discarded after training, and only the symbolic equation remains.

**This evaluation approach is consistent across all symbolic regression algorithms in SRBench** (DSR, AIFeynman, BSR, etc.) - they all evaluate the discovered symbolic equations rather than neural network outputs. The neural networks serve only as search mechanisms and are never evaluated for performance.

**Documentation Reference:** This is explicitly stated in the SRBench framework. According to the SRBench documentation (`CONTRIBUTING.md`, `CHANGES_AND_GUIDE.md`), algorithms must return a **sympy-compatible model string** for evaluation. The framework evaluates these symbolic equations, not the internal search mechanisms (neural networks, optimization algorithms, etc.) used during training. This is the standard evaluation protocol for all symbolic regression methods in SRBench (La Cava et al., NeurIPS 2021).

## Experimental Setup

**SRBench Configuration:**

We are using default SRBench settings except for the train/test split (80/20 instead of 75/25). The 80/20 split was chosen to match the GINN-LP comparison setup.

**Key Settings:**
- **Train/test split**: 80/20 (SRBench paper default: 75/25) - *Changed to match GINN-LP setup*
- **Number of trials**: 10 per dataset (matches SRBench paper)
- **Time limit**: 48:00 hours (matches SRBench paper black-box protocol)
- **Hyperparameter tuning**: Using `tuned.AIFeynman` which uses pre-tuned hyperparameters from the SRBench paper, so no additional tuning is needed
- **Target noise**: None (matches SRBench paper for black-box problems)
- **Feature noise**: None (matches SRBench paper)
- **Problem type**: Black-box (no `-sym_data` flag) - our datasets (ENB, Agriculture) are treated as black-box problems where the true underlying function is unknown

**Conclusion:** We are using default SRBench settings except for the 80/20 split, which was changed to match the GINN-LP comparison setup. Everything else (trials, time limits, hyperparameter tuning via `tuned.*` methods, no noise) matches the paper's black-box protocol (La Cava et al., NeurIPS 2021, Table 2).

## Dataset Information

This report evaluates AIFeynman (AI Feynman: A Physics-Inspired Method for Symbolic Regression) performance on two datasets:

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
| AIFeynman ENB | - | - | - | - | - | - | - | - | - | - | - | - |
| AIFeynman AGRIC 0.01 | - | - | - | - | - | - | - | - | - | - | - | - |
| AIFeynman AGRIC 0.1 | - | - | - | - | - | - | - | - | - | - | - | - |

## Notes

- Results pending - to be filled when AIFeynman experiments are completed.
