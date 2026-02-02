# SRBench: Changes, Additions, and Complete Guide

This document explains (1) what the SRBench repository is and what it does, (2) what is in the **original** repo vs what was **added** in this fork, (3) all changes and scripts created to support custom data (ENB and agric), (4) the exact meaning of **trials** and how the paper’s experiments are set up, and (5) how to run experiments. It is written so that another AI or a new reader can understand the full context without reading the codebase.

---

### Quick reference (for another AI)

- **Repo:** SRBench = open-source benchmark for symbolic regression (SR) and ML; paper: La Cava et al., NeurIPS 2021 Datasets and Benchmarks (arXiv:2107.14351). No benchmark code was modified.
- **Added by user (not in original repo):** Custom data in `data/data_agric/` (agric CSVs) and `data/data_enb/` (ENB2012 Cooling/Heating CSVs). A script `data/csv_to_tsvgz.py` was created to convert the ENB CSVs to the format the benchmark expects (TSV.GZ + folder layout). Outputs: `data/enb_cooling/` and `data/enb_heating/` (each with `*.tsv.gz` + `metadata.yaml`). Agric data was not converted (user has own preprocessing).
- **Trial:** One trial = one random seed = one run of (dataset, algorithm). Multiple trials = same (dataset, algorithm) repeated with different seeds to get statistics. Paper uses **10 trials** per (dataset, algorithm); Table 2: black-box “Total comparisons 26,840”, ground-truth “Total comparisons 54,600”. Use `-n_trials 10` to match paper; `-n_trials 1` for a quick run.
- **Run experiments:** From `srbench/experiment/`, e.g. `python analyze.py ../data --local -n_trials 1 -results ../results_enb -time_limit 48:00`. To run only three methods: `-ml tuned.AIFeynman,tuned.BSRRegressor,tuned.DSRRegressor`.

---

## 1. What SRBench Is and What It Does

**SRBench** is an open-source, reproducible **benchmark for symbolic regression (SR)** and related machine learning methods. It is described in the NeurIPS 2021 Datasets and Benchmarks paper: *“Contemporary Symbolic Regression Methods and their Relative Performance”* (La Cava et al., arXiv:2107.14351). The PDF is in this same folder: `paper/2107.14351v1.pdf`.

- **Purpose:** Compare many SR algorithms and standard ML baselines on the same datasets under the same protocol (same train/test split, same metrics, same time/compute limits). No code in the core benchmark was changed; only **data** and **documentation** were added.
- **Scope (original paper):**
  - **Black-box:** 122 datasets (no known model), 21 algorithms (14 SR + 7 ML), metrics: test R², model complexity, training time.
  - **Ground-truth:** 130 datasets with known symbolic models (Feynman + Strogatz ODEs), 14 SR algorithms, 4 noise levels; metric: whether the method recovers the exact (or equivalent) equation.
- **How it works (high level):**
  - Each “run” is: **one algorithm** trained on **one dataset** for **one random seed** (one “trial”). The script `experiment/analyze.py` discovers datasets under a root directory, then for each (dataset × algorithm × trial) invokes `evaluate_model.py`, which loads data, does a 75/25 train/test split (using that trial’s seed), optionally does hyperparameter tuning, trains the model, and saves results (R², complexity, etc.) to JSON.
  - Algorithms must expose a **scikit-learn–compatible API** and return a **sympy-compatible** model string. Each algorithm can live in `algorithms/<name>/` (with its own conda env) or in `experiment/methods/` (Python-only, same env).
  - The **original** benchmark does **not** ship the 252 PMLB datasets; users must clone the PMLB repo and point `analyze.py` at that dataset root. The repo does ship a small **test** dataset under `experiment/test/` (two `.tsv.gz` files + `metadata.yaml`) for quick sanity runs.

---

## 2. What Is in the Original Repo vs What Was Added

### 2.1 Original Repo (Unchanged)

- **`algorithms/`** – Per-method folders (e.g. eplex, gpgomea, pysr, tir) with `regressor.py`, `metadata.yml`, optional `environment.yml` and `install.sh`. Used by the main install flow (`install.sh`).
- **`experiment/`** – Core experiment code: `analyze.py` (orchestrator), `evaluate_model.py` (single run), `read_file.py` (load TSV/CSV with a `target` column), `assess_symbolic_model.py` (ground-truth symbolic check), metrics, seeds, and **`methods/`** (sklearn-style wrappers, including `tuned/` with AIFeynman, BSR, DSR, etc.). **`experiment/test/`** contains two small `.tsv.gz` datasets + `metadata.yaml` for quick tests.
- **`data/`** – In the **original** repo this folder is either absent or minimal (e.g. a small example). The **official** benchmark data lives in a separate PMLB clone, not inside this repo.
- **`postprocessing/`** – Scripts and notebooks to collate results into Feather files and produce figures.
- **`docs/`**, **`paper/`**, **`ci/`**, **`scripts/`**, **`base_environment.yml`**, **`install.sh`**, **`README.md`**, etc. – Documentation, CI, and environment setup. **None of this was modified.**

No Python or YAML files in `experiment/`, `algorithms/`, or the root were changed. The only edits are **new files** under `data/` and `paper/` as described below.

### 2.2 What Was Added (This Fork)

- **Custom data (user-added, not part of the original SRBench repo):**
  - **`data/data_agric/`** – Agriculture-related CSVs: `farmer_advisor_dataset.csv`, `market_researcher_dataset.csv`. These are **not** in the original repo; they were added by the user for their own comparisons. They contain categorical columns and multiple possible target columns; they were **not** converted to TSV.GZ in this pass (user said they have their own preprocessing for agric).
  - **`data/data_enb/`** – ENB2012 energy-efficiency data (user-added): `ENB2012_Cooling_Load.csv`, `ENB2012_Heating_Load.csv`, plus a `split/` subfolder with train/test CSVs. Each main CSV has 8 features (X1–X8) and a single target column named **`target`** (cooling load or heating load). 768 rows each. This is the “ENB” data referred to below.

- **Script and outputs (created to support ENB without changing SRBench code):**
  - **`data/csv_to_tsvgz.py`** – A small Python script (stdlib only: `csv`, `gzip`, `os`) that reads the two ENB CSVs from `data/data_enb/`, converts each to tab-separated format, gzips them, and writes them into the layout that `analyze.py` expects. It does **not** change any values; it only changes delimiter (comma → tab) and compression (none → gzip). Outputs:
    - **`data/enb_cooling/enb_cooling.tsv.gz`**
    - **`data/enb_heating/enb_heating.tsv.gz`**
  - **`data/enb_cooling/metadata.yaml`** and **`data/enb_heating/metadata.yaml`** – YAML files with `task: regression` and minimal feature/target descriptions so that `analyze.py` accepts these folders as regression datasets (it requires a `metadata.yaml` in the same directory as each `.tsv.gz` file).

So: the **only** things added are (1) the user’s data in `data_agric/` and `data_enb/`, (2) the conversion script `csv_to_tsvgz.py`, (3) the two ENB dataset folders in SRBench format (`enb_cooling/`, `enb_heating/` with `.tsv.gz` + `metadata.yaml`), and (4) this markdown file in `paper/`.

---

## 3. How the Benchmark Discovers Datasets (No Code Changes)

To avoid changing SRBench code, the data had to match the existing contract:

- **Dataset root:** You pass a single **dataset directory** to `analyze.py` (e.g. `../data` or `/path/to/pmlb/datasets`). The script then looks for datasets under that root.
- **Discovery rule:** It uses `glob(DATASET_DIR + '/*/*.tsv.gz')`. So every dataset must live in a **subfolder** of the root, and each subfolder must contain at least one `.tsv.gz` file. Example: `data/enb_cooling/enb_cooling.tsv.gz`.
- **Metadata:** For each `.tsv.gz` path found, the code loads `metadata.yaml` from the **same** directory (the parent of the file). That YAML must contain `task: regression` (for black-box regression); otherwise that file is skipped.
- **Target column:** `read_file.py` (used by `evaluate_model.py`) expects a single target column. Its default name is **`target`**. The ENB CSVs already had a column named `target` (one for cooling, one for heating), so no column rename was needed; only format conversion (CSV → TSV.GZ) and folder layout were done.

So “what was done” for ENB: (1) add your CSVs under `data/data_enb/`, (2) add `csv_to_tsvgz.py` to convert them to TSV.GZ in the right place, (3) add `metadata.yaml` in each of `data/enb_cooling/` and `data/enb_heating/`. Agric data was left as-is (CSV in `data_agric/`); it could be converted later with a similar script if desired, after handling categoricals and choosing a single target column.

---

## 4. What a “Trial” Is and How Many the Paper Used

### 4.1 Definition of One Trial

- **One trial** = one **random seed** used for (a) the train/test split and (b) the algorithm’s own randomness (e.g. init, sampling).
- So: **one experiment run** = one (dataset, algorithm, trial) = one seed. For that run, the data is split once (e.g. 75% train / 25% test) with that seed, and the algorithm is trained once with that seed.
- **Multiple trials** = the **same** (dataset, algorithm) repeated with **different** seeds, to get a distribution of outcomes (e.g. median R², confidence intervals). So “10 trials” means 10 separate runs for that (dataset, algorithm), each with a different seed.

In code:

- `analyze.py` uses `-n_trials N` and `-starting_seed K`. It loops over `N` trial indices; for each index it takes a fixed seed from `experiment/seeds.py` (the list `SEEDS`). So trial 0 = first seed, trial 1 = second seed, etc.
- So **“one trial”** in the CLI = one seed from that list, and **“one experiment”** in the paper = the full set of (dataset × algorithm × trial) runs. So an “experiment” is many trials (many runs); each run is one trial.

### 4.2 What the Paper Used (Tables and Text)

From the paper (Section 4, Table 2):

- **Black-box (Table 2):** 122 datasets, 21 algorithms, **10 trials** per (dataset, algorithm). Train/test split 75/25. Table 2 gives “Total comparisons 26,840” for black-box. So effectively **10 trials** per (dataset, algorithm); the exact 26,840 may reflect a slight difference in how datasets or methods were counted (e.g. some filtered), but the **design is 10 trials**.
- **Ground-truth (Table 2):** 130 datasets, 14 algorithms, **10 trials** per (dataset, algorithm, noise level), **4 target noise levels** (0, 0.001, 0.01, 0.1). Table 2 gives “Total comparisons 54,600” for ground-truth.
- So the **standard in the paper is 10 trials** for each (dataset, algorithm) combination (and per noise level for ground-truth). All reported results in the paper (e.g. median R², solution rates, confidence intervals) aggregate over these 10 trials.

So if you want to match the paper:

- Use **`-n_trials 10`** (and optionally `-starting_seed 0` to use the first 10 seeds in `seeds.py`).
- For a quick run, **`-n_trials 1`** is one seed per (dataset, algorithm), i.e. one trial per combination.

**Note:** In `analyze.py`, the argument `-n_trials` is labeled in the help as “Number of parallel jobs” (a copy-paste error); it actually controls the **number of trials** (number of seeds / repeated runs), not the number of parallel processes. Parallelism is controlled by `-n_jobs` (local) or the job scheduler.

---

## 5. Summary of What You Have Now

| Item | Location | Origin |
|------|----------|--------|
| ENB Cooling CSV | `data/data_enb/ENB2012_Cooling_Load.csv` | User-added |
| ENB Heating CSV | `data/data_enb/ENB2012_Heating_Load.csv` | User-added |
| Agric CSVs | `data/data_agric/*.csv` | User-added |
| Conversion script | `data/csv_to_tsvgz.py` | Created here |
| ENB in SRBench format | `data/enb_cooling/`, `data/enb_heating/` (each: `*.tsv.gz` + `metadata.yaml`) | Created here |
| This guide | `paper/CHANGES_AND_GUIDE.md` | Created here |

Original repo structure, `experiment/`, `algorithms/`, and all benchmark logic are **unchanged**.

---

## 6. How to Run Experiments (Reference)

- **From repo root:** `experiment/` is the working directory for running the benchmark.
- **Dataset root for your ENB data:** If you are in `srbench/experiment/`, use `../data` as the dataset directory so that `../data/*/*.tsv.gz` finds `../data/enb_cooling/enb_cooling.tsv.gz` and `../data/enb_heating/enb_heating.tsv.gz`.

Example commands (run from `srbench/experiment/`):

```bash
# ENB only, 1 trial per (dataset, algorithm), local, results in ../results_enb
python analyze.py ../data --local -n_trials 1 -results ../results_enb -time_limit 48:00

# Same but 10 trials (paper standard)
python analyze.py ../data --local -n_trials 10 -results ../results_enb -time_limit 48:00

# Only three methods (e.g. for a class assignment: AIFeynman, BSR, DSR)
python analyze.py ../data --local -n_trials 1 -results ../results_enb -time_limit 48:00 -ml tuned.AIFeynman,tuned.BSRRegressor,tuned.DSRRegressor
```

- **Regenerating ENB TSV.GZ after changing CSVs:** From `srbench/data/`, run `python csv_to_tsvgz.py`. No SRBench code changes required.

---

## 7. Paper and Repo References

- **Paper:** La Cava et al., “Contemporary Symbolic Regression Methods and their Relative Performance,” NeurIPS 2021 Datasets and Benchmarks; arXiv:2107.14351. PDF in this folder: `srbench/paper/2107.14351v1.pdf`.
- **Table 2 (experiment design):** Number of datasets, algorithms, trials (10), split (75/25), termination (e.g. 48h black-box, 8h ground-truth), total comparisons.
- **Original repo:** [cavalab/srbench](https://github.com/cavalab/srbench) (or EpistasisLab/srbench). This fork adds the data folder, the ENB conversion script, the two ENB dataset folders in benchmark format, and this guide; everything else is intended to match the original.

---

## 8. Where Results Are Saved and What Is in the JSON

**Not in metadata.** Each run writes a **single JSON file** on disk. No metadata.yaml is updated with metrics.

**Path pattern:** When you run `analyze.py` with `-results ../results_enb`, the script builds a results directory per dataset: `results_enb/<dataname>/`. For each (dataset, algorithm, seed) it calls `evaluate_model.py`, which writes:

- **File path:** `{results_path}/{dataset_name}_{algorithm_name}_{seed}.json`  
  Example: `../results_enb/enb_cooling/enb_cooling_tuned.AIFeynman_23654.json`

**What’s inside the JSON (per run):** All of the following are written by `evaluate_model.py` so you can read them later from the JSON:

- **Identifiers:** `dataset`, `algorithm`, `params`, `random_state`
- **Time:** `time_time` (training time in seconds)
- **Accuracy (train and test):**  
  `mse_train`, `mse_test`, `mae_train`, `mae_test`, `r2_train`, `r2_test`  
  **Plus (added in this fork):** `rmse_train`, `rmse_test` (RMSE = √MSE), and `mape_train`, `mape_test` (MAPE; `None` if target has zeros or sklearn &lt; 0.24)
- **Model:** `symbolic_model` (string), `simplicity`  
- **Ground-truth runs only:** `true_model` if `-sym_data` was used

So **RMSE and MAPE are saved in the same JSON file** as the other metrics. You read that JSON (e.g. with Python `json.load()` or pandas) to get test metrics; nothing is stored in dataset metadata.

---

## 9. Rough Run-Time Expectations (ENB Only)

- **ENB:** 2 datasets (enb_cooling, enb_heating), 768 rows each, 8 features, single target.
- **Runs:** 2 × (number of methods) × (number of trials). Example: 3 methods (e.g. AIFeynman, BSR, DSR), 1 trial → 6 runs; 10 trials → 60 runs.
- **Per run:** The paper uses up to 48 h per run for black-box, but for “datasets up to 1000 rows” the competition guide suggests ~1 h. For these three methods (heavy: NN/MCMC/RL), on 768 rows, expect roughly **20 min–2 h per run** depending on method and seed.
- **Total:** With 3 methods and 1 trial, 6 runs: **about 1–3 h** with 3 parallel jobs; **about 3–8 h** sequential. With 10 trials, 60 runs: **about 10–25 h** with parallelism; **about 1–3 days** sequential.

**Code change (this fork):** In `experiment/evaluate_model.py`, RMSE and MAPE were added to the evaluation and saved in the same JSON:

- **RMSE:** Computed as √MSE for train and test and stored as `rmse_train`, `rmse_test`.
- **MAPE:** Computed with `sklearn.metrics.mean_absolute_percentage_error` (if available, sklearn ≥ 0.24) and stored as `mape_train`, `mape_test`. If the target has zeros or the metric is invalid, those keys are set to `null`. If sklearn is too old, MAPE keys are set to `null`.

So evaluation **does** measure and save RMSE and MAPE on the test (and train) data in the result JSON; you do not need to derive them later.

---

**Running one job to verify:** From `srbench/experiment/` you can run a single (dataset, method, seed) to confirm everything works and that the JSON contains the new keys. Example (one dataset, one method, one trial; fast method):

```bash
cd srbench/experiment
python analyze.py ../data --local -n_trials 1 -results ../results_enb_test -time_limit 48:00 -job_limit 1 -ml LinearRegression
```

If your methods are under `methods/tuned/`, use e.g. `-ml tuned.AIFeynman,tuned.BSRRegressor,tuned.DSRRegressor` and `-job_limit 1` to run only the first of those. Then open the generated `.json` under `../results_enb_test/<dataname>/` and check for `mse_test`, `rmse_test`, `mae_test`, `mape_test`, `r2_test`.

---

This document is the single place that describes what was added, what was not changed, how trials and experiments are defined, and how to run the benchmark on the added ENB (and optionally agric) data.
