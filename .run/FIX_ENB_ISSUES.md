# ENB debugging notes for future assistants

This file is meant to brief another LLM (or human) on what is going wrong with ENB runs and how the environments are wired, so you don’t have to rediscover it from the logs.

## Context

- Project root: `/raid/hussein/project/srbench`
- ENB runs are launched via:
  - `.run/run_dsr_enb.sh` → `tuned.DSRRegressor`
  - `.run/run_bsr_enb.sh` → `tuned.BSRRegressor`
  - `.run/run_aifeynman_enb.sh` → `tuned.AIFeynman`
- Relevant logs:
  - `.logs/enb_heating_DSR.log`, `.logs/enb_cooling_DSR.log`
  - `.logs/enb_heating_BSR.log`, `.logs/enb_cooling_BSR.log`

## Observed symptoms in logs

### DSR (tuned.DSRRegressor)

- In `enb_heating_DSR.log` (and similarly for cooling) you see, for each of the 10 seeds:
  - `DSO subprocess warning/error in stderr:`
  - `DSO fit error: 'NoneType' object has no attribute 'execute'`
  - Traceback ends in `dso/dso/execute.py` at `cyfunc.execute(...)`.
- Despite these stderr messages, SRBench still logs a JSON `results` block per trial.
  - The learned `symbolic_model` is always `"x0"`.
  - Metrics are terrible (strongly negative `r2_*`), consistent with a degenerate model.
- Interpretation: the DSO inner run is crashing, the wrapper catches the error and returns a trivial model, so the pipeline “succeeds” but gives garbage results.

### BSR (tuned.BSRRegressor)

- In `enb_heating_BSR.log` / `enb_cooling_BSR.log` every job fails immediately with:
  - `ModuleNotFoundError: No module named 'bsr'`
  - Stack trace shows it comes from `experiment/methods/BSRRegressor.py`:
    - `from bsr.bsr_class import BSR`
- No BSR results are produced because the import never succeeds.

## Environment layout

- **Main SRBench env**: `srbench`
  - All `run_*` scripts do `conda activate srbench` then call `python analyze.py ...`.
  - `BSRRegressor.py` and `evaluate_model.py` execute inside this env.
- **DSO env**: `dso_env`
  - `experiment/methods/dso_bridge.py` hardcodes:
    - `DSO_PYTHON = "/raid/hussein/miniconda3/envs/dso_env/bin/python"`
  - DSO is *not* imported directly in `srbench`; instead, `DSRRegressor` calls `run_dso_fit(...)` which shells out into `dso_env` via this bridge.
- **AI‑Feynman envs**:
  - `aifeynman_env` and `env_alfey` exist under both `/home/hussein/miniconda3/envs/` and `/raid/hussein/miniconda3/envs/`.
  - `aifeynman_bridge.py` uses `/raid/hussein/miniconda3/envs/aifeynman_env/bin/python`.
- **BSR code & package**:
  - Repo cloned under: `srbench/z_codes/BSR` (upstream `MCMC-SymReg`).
  - `setup.py` defines a `bsr` package with `package_dir={'bsr': 'codes'}`.
  - `experiment/methods/BSRRegressor.py` does `from bsr.bsr_class import BSR`, i.e. it expects `bsr` to be importable **inside the `srbench` env**. There is no separate `bsr_env`.

## Likely root causes

1. **BSR: `ModuleNotFoundError: No module named 'bsr'`**
   - The `bsr` package has *not* been installed into the `srbench` conda env.
   - Fix is simply to install it in editable mode from `z_codes/BSR`.

2. **DSR: `AttributeError: 'NoneType' object has no attribute 'execute'`**
   - In `z_codes/DSR/dso/dso/execute.py`, the Cython extension is imported as:
     - `from dso import cyfunc`
   - When the extension is missing or broken, `cyfunc` can be `None`.
   - Original `cython_execute` unconditionally did:
     - `return cyfunc.execute(X, len(traversal), traversal, is_input_var)`
   - Result: during training, calling `cython_execute` would raise exactly the `'NoneType' object has no attribute 'execute'` error you see in stderr.
   - `dso_runner.py` catches exceptions, prints the error to stderr, and then writes a trivial result (`model: "x0"`, `complexity: 0`) to `result.json`. That’s why the pipeline does not crash, but produces useless models.

## Code changes already made in this branch

- **DSO fallback fix**
  - File: `/raid/hussein/project/srbench/z_codes/DSR/dso/dso/execute.py`
  - `cython_execute` has been modified to:
    - Check `if cyfunc is None: return python_execute(traversal, X)` before trying to use `cyfunc.execute(...)`.
    - This means if the Cython module isn’t available, DSO still runs (much slower) using the pure‑Python executor, instead of throwing the AttributeError.

- **Helper install script**
  - File: `.run/install_dependencies.sh`
  - Does two things:
    1. Activates `srbench` and runs `pip install -e .` in `z_codes/BSR` (installs `bsr` into the main env).
    2. Activates `dso_env` and runs `pip install -e ./dso --force-reinstall --no-deps` in `z_codes/DSR` (rebuilds the DSO Cython extension).

## How to get back to a healthy state

### Option 1: Run the installation script (recommended)

```bash
cd /raid/hussein/project/srbench
bash .run/install_dependencies.sh
```

Then rerun the ENB experiments:

```bash
bash .run/run_bsr_enb.sh
bash .run/run_dsr_enb.sh
```

You should:
- Stop seeing `ModuleNotFoundError: No module named 'bsr'` in the BSR logs.
- Stop seeing `'NoneType' object has no attribute 'execute'` from `cyfunc.execute` in the DSR stderr (either because Cython is rebuilt, or because the Python fallback kicks in).

### Option 2: Manual installation

**Install BSR into `srbench`:**

```bash
conda activate srbench
cd /raid/hussein/project/srbench/z_codes/BSR
pip install -e .
```

**Rebuild DSO Cython extension in `dso_env`:**

```bash
conda activate dso_env
cd /raid/hussein/project/srbench/z_codes/DSR
pip install -e ./dso --force-reinstall --no-deps
```

## Checks for a future LLM

When debugging further, it’s worth explicitly verifying:

- **Which `dso_env` is used**  
  - `dso_bridge.py` currently points to `/raid/hussein/miniconda3/envs/dso_env/bin/python`.  
  - Make sure *that exact* env has DSO installed (`pip show dso` or try `python -c "import dso"` inside it).

- **That the `execute.py` guard is actually in effect**  
  - Open the `execute.py` from the env used by `dso_env` and confirm `cython_execute` contains the `if cyfunc is None: return python_execute(...)` guard.
  - If not, the env might have an older copy of DSO; reinstall from `z_codes/DSR`.

- **That `bsr` is visible in the `srbench` env**  
  - In the `srbench` env, run:
    ```bash
    python -c "import bsr, sys; print('bsr:', bsr.__file__, '\\npython:', sys.executable)"
    ```
  - If this still raises `ModuleNotFoundError`, the editable install from `z_codes/BSR` didn’t succeed or was done in the wrong env.
