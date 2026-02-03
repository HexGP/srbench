#!/bin/bash
# Commands to run BSR on Agriculture datasets (0.01 sample) with SRBench
# Data split: 80/20 train/test (SRBench uses 75/25 internally, but random_state ensures reproducibility)
# Random state: Uses SRBench's seed list (seeds.py) for consistency
# Note: Uses Option 2 - merged datasets with all features, single-target, 0.01 sample fraction

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing bsr_agric_001 windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' bsr_agric_001$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for BSR Agriculture 0.01 experiments
tmux new-window -t srbench -n bsr_agric_001 -d
sleep 1  # Give tmux time to create the window

# Build commands and execute Agriculture datasets in tmux window
tmux send-keys -t srbench:bsr_agric_001 "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:bsr_agric_001 "conda activate srbench" C-m
tmux send-keys -t srbench:bsr_agric_001 "echo 'Starting BSR on AGRICULTURE SUSTAINABILITY (0.01 sample) dataset...'" C-m
tmux send-keys -t srbench:bsr_agric_001 "python analyze.py ../data/agric_001_sustainability/agric_001_sustainability.tsv.gz --local -n_trials 10 -results ../results_agric_001 -time_limit 48:00 -ml tuned.BSRRegressor -n_jobs 16 > ../data/agric_001_sustainability/agric_001_sustainability_BSR.log 2>&1 &" C-m
tmux send-keys -t srbench:bsr_agric_001 "echo 'Starting BSR on AGRICULTURE CONSUMER_TREND (0.01 sample) dataset...'" C-m
tmux send-keys -t srbench:bsr_agric_001 "python analyze.py ../data/agric_001_consumer_trend/agric_001_consumer_trend.tsv.gz --local -n_trials 10 -results ../results_agric_001 -time_limit 48:00 -ml tuned.BSRRegressor -n_jobs 16 > ../data/agric_001_consumer_trend/agric_001_consumer_trend_BSR.log 2>&1 &" C-m
tmux send-keys -t srbench:bsr_agric_001 "echo 'All Agriculture (0.01) BSR experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:bsr_agric_001 "wait" C-m
tmux send-keys -t srbench:bsr_agric_001 "echo 'Agriculture (0.01) BSR experiments completed'" C-m

echo "BSR Agriculture (0.01 sample) experiments started in tmux session 'srbench', window 'bsr_agric_001'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:bsr_agric_001"
