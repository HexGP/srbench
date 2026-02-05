# Agriculture LOG pipeline – strategy for another LLM

This doc explains **what** the Agriculture “log” pipeline is, **why** it exists, **where** everything lives, and **what to do** so another LLM (or human) can run and compare fairly.

---

## 1. Goal

We compare **GINN-LP / MTRGINN-LP** (codes) with **SRBench methods** (DSR, BSR, AI-Feynman) on the **Agriculture** dataset. For a **fair comparison**, metrics must be in the **same scale**:

- **GINN-LP and MTRGINN-LP (codes)** train and evaluate on **transformed** targets (same transform as in `codes/Agriculture/mtr_ginn_agric_sym.py`). Reported MAE, MAPE, RMSE are in that transformed space.
- **SRBench by default** uses **raw** targets and reports metrics in **original** scale.

So we added a **second, parallel** Agriculture pipeline in SRBench that applies the **same target transform** and writes **LOG datasets**. Running SRBench on those gives metrics in the **same space** as GINN-LP/MTRGINN-LP.

**Do not remove or replace the original pipeline.** The log pipeline is an **additional** path.

---

## 2. What exists (map)

| What | Location | Role |
|------|----------|------|
| **Original agric data (raw targets)** | `srbench/data/csv_to_tsvgz_agric.py` | Builds `agric_001_*`, `agric_01_*` (no transform). |
| **LOG agric data (transformed targets)** | `srbench/data/csv_to_tsvgz_agric_log.py` | Builds `agric_001_*_log`, `agric_01_*_log` (targets transformed like codes). |
| **Original run scripts** | `srbench/.run/*.sh` | DSR/BSR/AIFeynman on **raw** agric (and ENB). No `_log` in name. |
| **LOG run scripts** | `srbench/.run_log/*.sh` | DSR/BSR/AIFeynman on **LOG** agric only. All scripts have `_log` in name. |
| **Original results** | `srbench/results_agric_001/`, `srbench/results_agric_01/` | From `.run` scripts; metrics in **original** scale. |
| **LOG results** | `srbench/results_agric_001_log/`, `srbench/results_agric_01_log/` | From `.run_log` scripts; metrics in **transformed** scale (comparable to GINN-LP). |
| **Short README** | `srbench/data/README_AGRIC_LOG.md` | How to build LOG datasets and where run scripts live. |

Transform used in codes and in LOG pipeline: same as in `codes/Agriculture/mtr_ginn_agric_sym.py` (targets transformed before train/test; no inverse when reporting metrics).

---

## 3. What another LLM needs to do

### To **generate** the LOG datasets (once)

- **Where:** `srbench/data/`
- **Commands:**
  - `python csv_to_tsvgz_agric_log.py 0.01` → creates `agric_001_sustainability_log`, `agric_001_consumer_trend_log`
  - `python csv_to_tsvgz_agric_log.py 0.1`  → creates `agric_01_sustainability_log`, `agric_01_consumer_trend_log`
- **Requires:** Same inputs as original pipeline (e.g. `data_agric/farmer_advisor_dataset.csv`, `market_researcher_dataset.csv`). No changes to the original `csv_to_tsvgz_agric.py`.

### To **run** SRBench on LOG datasets (fair comparison with GINN-LP)

- **Where:** Scripts live in `srbench/.run_log/`
- **Scripts (run from repo root or from `srbench/`):**
  - `run_dsr_agric_001_log.sh`, `run_dsr_agric_01_log.sh`
  - `run_bsr_agric_001_log.sh`, `run_bsr_agric_01_log.sh`
  - `run_aifeynman_agric_001_log.sh`, `run_aifeynman_agric_01_log.sh`
- **Example:** `bash srbench/.run_log/run_dsr_agric_001_log.sh`
- **Output:** Results under `srbench/results_agric_001_log/` and `srbench/results_agric_01_log/`. Use these when comparing to GINN-LP/MTRGINN-LP Agriculture metrics.

### To **compare** numbers

- **GINN-LP / MTRGINN-LP:** Metrics in JSON outputs (e.g. in `ginn-lp/run_AGRIC/outputs/`) are in **transformed** space.
- **SRBench LOG runs:** Metrics in `results_agric_*_log/` are in the **same transformed** space. Compare these to GINN-LP/MTRGINN-LP.
- **SRBench original runs:** Metrics in `results_agric_001/`, `results_agric_01/` are in **original** scale. Do **not** compare these directly to GINN-LP Agriculture numbers (different scale).

---

## 4. Summary for an LLM

1. **Two pipelines:** Original (raw targets, `srbench/.run/`, `csv_to_tsvgz_agric.py`) and LOG (transformed targets, `srbench/.run_log/`, `csv_to_tsvgz_agric_log.py`). Keep both.
2. **LOG run scripts** are only in `srbench/.run_log/`. They point at `*_log` datasets and `results_agric_*_log/`.
3. **Fair comparison with GINN-LP/MTRGINN-LP:** Use LOG data and LOG run scripts; use metrics from `results_agric_*_log/`.
4. **Building LOG data:** Run `csv_to_tsvgz_agric_log.py` with `0.01` and `0.1` from `srbench/data/`; no changes to original script or data layout.
