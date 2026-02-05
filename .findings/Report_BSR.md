# BSRRegressor Performance Report

## Evaluation Method

**Critical Clarification: Search Mechanisms vs. Symbolic Model Evaluation**

**The search mechanisms (including any neural networks) are NOT being evaluated and have NO metrics.**

The performance metrics reported in this document (MAE, MAPE, RMSE, MSE) are **exclusively for the discovered symbolic equations**, not the search mechanisms or neural networks used during training.

**How BSRRegressor Works:**
- **During Training**: Bayesian optimization and tree-based search methods guide the discovery of symbolic expressions. These search mechanisms act as tools to find good symbolic expressions only.
- **During Evaluation**: The discovered symbolic equation is evaluated directly using symbolic execution.

**Key Points:**
1. **Search Mechanism Role**: The search mechanisms (Bayesian optimization, tree-based methods, etc.) are used solely as tools to find good symbolic expressions. They are never evaluated for performance metrics.
2. **Symbolic Model Evaluation**: Once training completes, the best symbolic equation is extracted. This symbolic equation is what gets evaluated to produce all the metrics (MAE, MAPE, RMSE, MSE) reported in this document.
3. **No Search Mechanism Metrics**: There are no separate metrics for the search mechanisms. The search mechanisms are discarded after training, and only the symbolic equation remains.

**This evaluation approach is consistent across all symbolic regression algorithms in SRBench** (DSR, AIFeynman, BSR, etc.) - they all evaluate the discovered symbolic equations rather than the search mechanisms or neural network outputs. The search mechanisms serve only as tools to discover symbolic expressions and are never evaluated for performance.

**Documentation Reference:** This is explicitly stated in the SRBench framework. According to the SRBench documentation (`CONTRIBUTING.md`, `CHANGES_AND_GUIDE.md`), algorithms must return a **sympy-compatible model string** for evaluation. The framework evaluates these symbolic equations, not the internal search mechanisms (neural networks, optimization algorithms, etc.) used during training. This is the standard evaluation protocol for all symbolic regression methods in SRBench (La Cava et al., NeurIPS 2021).

## Experimental Setup

**SRBench Configuration:**

We are using default SRBench settings except for the train/test split (80/20 instead of 75/25). The 80/20 split was chosen to match the GINN-LP comparison setup.

**Key Settings:**
- **Train/test split**: 80/20 (SRBench paper default: 75/25) - *Changed to match GINN-LP setup*
- **Number of trials**: 10 per dataset (matches SRBench paper)
- **Time limit**: 48:00 hours (matches SRBench paper black-box protocol)
- **Hyperparameter tuning**: Using `tuned.BSRRegressor` which uses pre-tuned hyperparameters from the SRBench paper, so no additional tuning is needed
- **Target noise**: None (matches SRBench paper for black-box problems)
- **Feature noise**: None (matches SRBench paper)
- **Problem type**: Black-box (no `-sym_data` flag) - our datasets (ENB, Agriculture) are treated as black-box problems where the true underlying function is unknown

**Conclusion:** We are using default SRBench settings except for the 80/20 split, which was changed to match the GINN-LP comparison setup. Everything else (trials, time limits, hyperparameter tuning via `tuned.*` methods, no noise) matches the paper's black-box protocol (La Cava et al., NeurIPS 2021, Table 2).

## Dataset Information

This report evaluates BSRRegressor (Bayesian Symbolic Regression) performance on two datasets:

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
| BSR ENB | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* | N/A* |
| BSR AGRIC 0.01 | - | - | - | - | - | - | - | - | - | - | - | - |
| BSR AGRIC 0.1 | - | - | - | - | - | - | - | - | - | - | - | - |

\* **ENB Results Unavailable**: All runs failed due to numerical instability errors (SVD convergence failure). See "Known Issues" section below for details.

## Known Issues: Numerical Instability on ENB Datasets

**Status:** BSRRegressor encounters numerical instability errors when training on ENB datasets, preventing successful completion of experiments.

### Error Details

BSRRegressor fails during training with the following errors:

1. **Fatal Error: SVD Convergence Failure**
   - **Location**: `funcs.py:1226` in `newProp()` function
   - **Error**: `numpy.linalg.LinAlgError: SVD did not converge`
   - **Cause**: The algorithm attempts to compute `np.linalg.matrix_rank(new_outputs)` where `new_outputs` is an ill-conditioned matrix (very large condition number) or contains NaN/Inf values from previous numerical overflows. The SVD algorithm fails to converge on this matrix.
   - **Impact**: Training crashes immediately with no error recovery mechanism in the BSR implementation.

2. **Runtime Warnings (Non-Fatal but Indicative)**
   - **Divide by zero in log**: Multiple warnings about `divide by zero encountered in log` when computing log probabilities with very small or zero variance values (`old_sa2`, `old_sb2`) in the Bayesian inference calculations.
   - **Overflow in square/power**: Warnings about `overflow encountered in square` and `overflow encountered in power` when evaluating symbolic expressions that produce extreme values.
   - **Invalid values in sin/cos**: Warnings about `invalid value encountered in sin/cos` due to NaN values propagating from previous numerical overflows.

### Root Cause

The numerical instability appears to be an inherent limitation of the BSR implementation:
- **Ill-conditioned matrices**: The MCMC sampling process generates symbolic expressions that, when evaluated, produce matrices with very large condition numbers.
- **Numerical overflow**: Intermediate calculations in the symbolic expression evaluation produce values that exceed floating-point precision limits.
- **No error handling**: The BSR code does not include try-except blocks to catch and recover from these numerical errors.

### Hyperparameters Used

The errors occur with the `tuned.BSRRegressor` configuration:
- `itrNum=7071` (scaled from base 5000)
- `val=141` (scaled from base 100)
- `treeNum=3`
- `alpha1=0.4`, `alpha2=0.4`, `beta=-1`

### Impact on Results

- **ENB Datasets**: All 10 trials per target (20 total runs) fail with the SVD convergence error. No successful runs were obtained for ENB Heating Load or Cooling Load.
- **Agriculture Datasets**: Testing pending - will be evaluated separately to determine if the numerical instability is dataset-specific or algorithm-wide.

### Why BSR Fails While DSR Succeeds: Fundamental Algorithmic Differences

**Dataset preparation is NOT the issue** - both algorithms receive identically preprocessed data from SRBench. The failure is due to fundamental differences in how BSR and DSR operate:

#### BSR's Multi-Tree Ensemble Approach (Vulnerable to Numerical Issues)

BSR uses an **ensemble of K trees** (default K=3) that are combined via linear regression:

1. **Multiple Tree Evaluation**: BSR maintains K separate symbolic trees simultaneously (lines 147-151 in `bsr_class.py`):
   ```python
   XX = np.zeros((n_train, K))  # Matrix: (n_samples, K_trees)
   for count in np.arange(K):
       temp = allcal(RootLists[count][-1], train_data)  # Evaluate each tree
       XX[:, count] = temp  # Each column is one tree's output
   ```

2. **Matrix Rank Check (Critical Failure Point)**: Before accepting a new tree proposal, BSR **must** check if the K tree outputs are linearly independent (line 1226 in `funcs.py`):
   ```python
   if np.linalg.matrix_rank(new_outputs) < K:  # ← FAILS HERE
       return [False, ...]  # Reject proposal if rank < K
   ```
   - **Why this matters**: If the K tree outputs are linearly dependent, the linear regression coefficients cannot be uniquely determined.
   - **The problem**: When symbolic expressions produce extreme values (overflow) or NaN, the `new_outputs` matrix becomes ill-conditioned, causing SVD to fail.

3. **Linear Regression Combination**: The K tree outputs are combined via least squares:
   ```python
   Beta = np.linalg.inv(np.matmul(XX.transpose(), XX)+epsilon)
   output = np.matmul(XX, Beta)  # Final prediction = weighted sum of K trees
   ```

#### DSR's Single-Program Approach (More Robust)

DSR evaluates **one symbolic program at a time** using reinforcement learning:

1. **Single Program Evaluation**: DSR evaluates one program via `p.execute(X_train)` and computes a simple fitness metric (e.g., neg_nrmse):
   ```python
   y_hat = p.execute(self.X_train)  # Single program evaluation
   r = self.metric(self.y_train, y_hat)  # Simple error metric
   ```

2. **No Matrix Operations**: DSR does **not** need to:
   - Compute matrix ranks
   - Check linear independence
   - Solve linear systems with multiple components

3. **Built-in Error Handling**: DSR has explicit handling for invalid expressions:
   ```python
   if p.invalid:  # Catches NaN/Inf gracefully
       return self.invalid_reward
   ```

#### Why ENB Dataset Triggers BSR's Failure

The ENB dataset characteristics that make BSR vulnerable:

1. **Feature Interactions**: ENB has 8 features with complex interactions. When BSR's MCMC sampling generates symbolic expressions with operations like `exp`, `square`, `cubic`, `inv`, these can produce extreme values when combined.

2. **Multi-Tree Complexity**: With K=3 trees, BSR must ensure all three trees produce linearly independent outputs. If any tree produces extreme values or NaN, the entire `new_outputs` matrix becomes ill-conditioned.

3. **MCMC Sampling**: During the MCMC proposal step, BSR randomly modifies tree structures. Some proposals generate expressions that evaluate to extreme values (overflow in `square`, `cubic`, `inv`), which then propagate into the matrix rank computation.

#### Why DSR Handles ENB Successfully

1. **Single Expression**: DSR only needs to evaluate one expression at a time, so numerical issues are isolated to that specific program.

2. **RL-Guided Search**: The neural network policy learns to avoid expressions that produce invalid outputs, naturally steering away from problematic regions of the search space.

3. **No Matrix Rank Requirement**: DSR doesn't need to check linear independence, so it never encounters the SVD convergence issue.

#### Conclusion

The failure is **algorithmic, not data-related**. BSR's requirement to maintain K linearly independent tree outputs and compute matrix ranks makes it fundamentally more vulnerable to numerical instability than DSR's single-program approach. This is an inherent limitation of BSR's ensemble-based architecture when dealing with datasets that produce extreme values in symbolic expression evaluation.

**For a detailed concrete example** showing how BSR and DSR process a single ENB data row differently, see `BSR_vs_DSR_Example.md` in this directory.

### Decision: No Algorithm Modifications

**We are not modifying the BSR algorithm to fix these errors** because:
1. **Fair Comparison**: Our goal is to compare results as-is with the original implementations. Modifying the algorithm to add error handling or numerical stability improvements would change its behavior and defeat the purpose of a fair comparison.
2. **Baseline Accuracy**: We want to report the actual performance (or failures) of the algorithm as implemented, not a modified version.
3. **Reproducibility**: Keeping the algorithm unchanged ensures our results can be compared directly with other studies using the same BSR implementation.

### Notes

- **ENB Results**: No successful runs obtained due to numerical instability errors.
- **Agriculture Results**: Pending - experiments will be run separately to assess whether the numerical issues are dataset-specific.
- **Error Logs**: Detailed error traces are available in `srbench/data/enb_heating/enb_heating_BSR.log` and `srbench/data/enb_cooling/enb_cooling_BSR.log`.
