#!/bin/bash
# DSR baseline sweep: ENB + Agriculture (sample_fraction=0.01, ~2501 rows, the
# authoritative fraction per paper_targets.md STEP 0), seed positions {0,1,2}
# (SRBench SEEDS[0..2] = 23654, 15795, 860), tuned.DSRRegressor (8h max_time,
# graceful DSO stop-on-timeout fix already applied in z_codes/DSR/dso).
#
# --noskips forces a fresh run even though stale pre-fix result files exist
# for these same seeds (some Agriculture sustainability runs previously fell
# back to x0 under the old 1h effective cap).
set -uo pipefail
cd /raid/hussein/project/srbench/experiment

source /home/hussein/miniconda3/etc/profile.d/conda.sh
conda activate srbench

export DSR_PATH=$(cd .. && pwd)/z_codes/DSR/dso
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-2}"
mkdir -p ../.logs

echo "[$(date)] Starting DSR baseline sweep (ENB + Agriculture, seeds 0,1,2)"

python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local --noskips -n_trials 3 -starting_seed 0 -results ../.results -ml tuned.DSRRegressor -n_jobs 3 > ../.logs/baseline_enb_heating_DSR.log 2>&1 &
python analyze.py ../data/enb_cooling/enb_cooling.tsv.gz --local --noskips -n_trials 3 -starting_seed 0 -results ../.results -ml tuned.DSRRegressor -n_jobs 3 > ../.logs/baseline_enb_cooling_DSR.log 2>&1 &
python analyze.py ../data/agric_001_sustainability/agric_001_sustainability.tsv.gz --local --noskips -n_trials 3 -starting_seed 0 -results ../.results -ml tuned.DSRRegressor -n_jobs 3 > ../.logs/baseline_agric_001_sustainability_DSR.log 2>&1 &
python analyze.py ../data/agric_001_consumer_trend/agric_001_consumer_trend.tsv.gz --local --noskips -n_trials 3 -starting_seed 0 -results ../.results -ml tuned.DSRRegressor -n_jobs 3 > ../.logs/baseline_agric_001_consumer_trend_DSR.log 2>&1 &

wait
echo "[$(date)] DSR baseline sweep complete"
