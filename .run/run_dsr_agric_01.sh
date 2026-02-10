#!/bin/bash
# Commands to run DSRRegressor on Agriculture datasets (0.1 sample) with SRBench
# Data split: 80/20 train/test (SRBench uses 80/20 split internally, random_state ensures reproducibility)
# Random state: Uses SRBench's seed list (seeds.py) for consistency
# Note: Uses Option 2 - merged datasets with all features, single-target, 0.1 sample fraction

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing dsr_agric_01 windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' dsr_agric_01$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for DSR Agriculture 0.1 experiments
tmux new-window -t srbench -n dsr_agric_01 -d
sleep 1  # Give tmux time to create the window

# Build commands and execute Agriculture datasets in tmux window
tmux send-keys -t srbench:dsr_agric_01 "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:dsr_agric_01 "conda activate srbench" C-m
tmux send-keys -t srbench:dsr_agric_01 "mkdir -p ../.logs" C-m
tmux send-keys -t srbench:dsr_agric_01 "echo 'Starting DSRRegressor on AGRICULTURE SUSTAINABILITY (0.1 sample) dataset...'" C-m
tmux send-keys -t srbench:dsr_agric_01 "python analyze.py ../data/agric_01_sustainability/agric_01_sustainability.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../.logs/agric_01_sustainability_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr_agric_01 "echo 'Starting DSRRegressor on AGRICULTURE CONSUMER_TREND (0.1 sample) dataset...'" C-m
tmux send-keys -t srbench:dsr_agric_01 "python analyze.py ../data/agric_01_consumer_trend/agric_01_consumer_trend.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../.logs/agric_01_consumer_trend_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr_agric_01 "echo 'All Agriculture (0.1) DSRRegressor experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:dsr_agric_01 "wait" C-m
tmux send-keys -t srbench:dsr_agric_01 "echo 'Agriculture (0.1) DSRRegressor experiments completed'" C-m

echo "DSRRegressor Agriculture (0.1 sample) experiments started in tmux session 'srbench', window 'dsr_agric_01'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:dsr_agric_01"
