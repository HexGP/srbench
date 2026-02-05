# Concrete Example: BSR vs DSR Processing a Single ENB Data Row

## Sample ENB Data Row

**Input Features:**
```
X1 = 0.98   (Relative Compactness)
X2 = 514.5  (Surface Area)
X3 = 294.0  (Wall Area)
X4 = 110.25 (Roof Area)
X5 = 7.0    (Overall Height)
X6 = 2.0    (Orientation)
X7 = 0.0    (Glazing Area)
X8 = 0.0    (Glazing Area Distribution)
```

**Target:**
```
y = 21.33  (Cooling Load)
```

---

## How BSR Processes This Row

### Step 1: BSR Maintains K=3 Trees Simultaneously

BSR maintains **3 separate symbolic trees** that are evaluated and combined:

**Tree 1 (example):** `exp(X2 * X3)`
- Evaluation: `exp(514.5 * 294.0)` = `exp(151,263)`
- **Problem**: This exceeds BSR's overflow threshold (200)
- BSR code (line 185-188 in `funcs.py`):
  ```python
  if node.data[i, 0] <= 200:
      node.data[i, 0] = np.exp(node.data[i, 0])
  else:
      node.data[i, 0] = 1e+10  # ← Capped at 1e+10
  ```
- **Result**: Tree 1 output = `1e+10` (extreme value)

**Tree 2 (example):** `square(X4)`
- Evaluation: `square(110.25)` = `12,155.06`
- **Result**: Tree 2 output = `12,155.06` (reasonable value)

**Tree 3 (example):** `inv(X7 + 0.1)`  (adding small constant to avoid exact zero)
- Evaluation: `inv(0.0 + 0.1)` = `inv(0.1)` = `10.0`
- **Result**: Tree 3 output = `10.0` (reasonable value)

### Step 2: BSR Forms Output Matrix

BSR creates a matrix where each **column** is one tree's output across all training samples:

```python
# For this single row, but BSR processes all 614 training rows simultaneously:
new_outputs = np.array([
    [1e+10,  12155.06,  10.0],  # Row 0 (this data point)
    [1e+10,  12155.06,  10.0],  # Row 1 (another data point)
    [1e+10,  12155.06,  10.0],  # Row 2
    # ... 611 more rows ...
])
# Shape: (614, 3) - 614 samples × 3 trees
```

### Step 3: BSR Checks Matrix Rank (FAILURE POINT)

BSR **must** check if the 3 tree outputs are linearly independent:

```python
# Line 1226 in funcs.py:
if np.linalg.matrix_rank(new_outputs) < K:  # K = 3
    return [False, ...]  # Reject proposal
```

**The Problem:**
- Tree 1 produces extreme values (`1e+10`) that dominate the matrix
- The matrix becomes **ill-conditioned** (very large condition number)
- When NumPy tries to compute SVD for matrix rank:
  ```python
  S = svd(new_outputs, compute_uv=False)  # ← FAILS HERE
  ```
- **Error**: `numpy.linalg.LinAlgError: SVD did not converge`

**Why it fails:**
- The extreme values (`1e+10`) create numerical instability in the SVD algorithm
- The matrix condition number is too large for SVD to converge
- BSR has no error handling, so training crashes

### Step 4: What BSR Would Do (If It Didn't Crash)

If the matrix rank check passed, BSR would:
1. Combine the 3 trees via linear regression:
   ```python
   XX = np.concatenate([[1], new_outputs], axis=1)  # Add constant term
   Beta = np.linalg.inv(XX.T @ XX + epsilon) @ XX.T @ y
   prediction = XX @ Beta
   ```
2. Final prediction = `Beta[0] + Beta[1]*Tree1 + Beta[2]*Tree2 + Beta[3]*Tree3`

---

## How DSR Processes This Row

### Step 1: DSR Evaluates One Program at a Time

DSR evaluates **one symbolic program** and computes its fitness:

**Example Program:** `X1 * X2 + X3`
- Evaluation: `0.98 * 514.5 + 294.0` = `798.21`
- **Result**: Program output = `798.21`

### Step 2: DSR Computes Simple Fitness Metric

DSR computes a simple error metric (e.g., neg_nrmse):

```python
# DSR code (regression.py):
y_hat = p.execute(X_train)  # Single program evaluation
r = self.metric(self.y_train, y_hat)  # Simple error metric
```

**For this row:**
- Prediction: `798.21`
- Target: `21.33`
- Error: `|798.21 - 21.33| = 776.88`
- This is a **bad program**, so DSR's RL policy will learn to avoid similar programs

### Step 3: DSR Handles Invalid Programs Gracefully

If a program produces NaN/Inf (e.g., `exp(X2 * X3)` without overflow protection):

```python
# DSR code (program.py):
if p.invalid:  # Checks for NaN/Inf
    return self.invalid_reward  # Returns -1.0 or similar
```

**Key Difference:**
- DSR **doesn't crash** - it just marks the program as invalid and continues
- No matrix operations needed
- No SVD computation required

### Step 4: DSR's RL Policy Learns to Avoid Bad Programs

The neural network policy learns:
- Programs like `exp(X2 * X3)` → produce extreme values → low reward
- Programs like `X1 * X2 + X3` → produce reasonable values → higher reward (even if not perfect)
- Over time, the policy steers away from problematic expressions

---

## Key Differences Summary

| Aspect | BSR | DSR |
|--------|-----|-----|
| **Number of expressions** | K=3 trees simultaneously | 1 program at a time |
| **Evaluation** | All K trees → matrix `(n_samples, K)` | Single program → vector `(n_samples,)` |
| **Critical operation** | **Matrix rank via SVD** | Simple error metric |
| **Failure mode** | SVD fails on ill-conditioned matrix → **crashes** | Invalid program → returns invalid_reward → **continues** |
| **Error handling** | **None** - crashes immediately | Built-in - marks invalid and continues |
| **Extreme values** | One tree with extreme values → entire matrix ill-conditioned → crash | One program with extreme values → marked invalid → next program |

---

## Why ENB Dataset Triggers BSR's Failure

1. **Large feature values**: X2=514.5, X3=294.0 → `X2 * X3 = 151,263`
2. **Operations like `exp`**: `exp(151,263)` → overflow → capped at `1e+10`
3. **Multi-tree requirement**: BSR needs all 3 trees to be linearly independent
4. **Matrix rank check**: When Tree 1 produces `1e+10`, the matrix becomes ill-conditioned
5. **SVD failure**: NumPy's SVD cannot converge on the ill-conditioned matrix
6. **No recovery**: BSR has no error handling, so training crashes

## Why DSR Handles ENB Successfully

1. **Single program**: Only evaluates one expression at a time
2. **No matrix operations**: Doesn't need to check linear independence
3. **Graceful degradation**: Invalid programs return a low reward but don't crash
4. **RL learning**: Policy learns to avoid problematic expressions over time
5. **Isolated failures**: One bad program doesn't affect the entire training process

---

## Conclusion

The failure is **algorithmic, not data-related**. BSR's requirement to:
- Maintain K linearly independent tree outputs
- Compute matrix rank via SVD on potentially ill-conditioned matrices
- Combine trees via linear regression

...makes it fundamentally vulnerable to numerical instability when symbolic expressions produce extreme values.

DSR's simpler approach:
- Evaluate one program at a time
- Compute simple error metrics
- Handle invalid programs gracefully

...makes it more robust to the same numerical issues.
