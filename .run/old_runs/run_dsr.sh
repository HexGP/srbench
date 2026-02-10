#!/bin/bash
# Commands to run DSRRegressor on ENB and Agriculture datasets with SRBench
# Data split: 80/20 train/test (SRBench uses 75/25 internally, but random_state ensures reproducibility)
# Random state: Uses SRBench's seed list (seeds.py) for consistency

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing dsr windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' dsr$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for DSR experiments
tmux new-window -t srbench -n dsr -d
sleep 1  # Give tmux time to create the window

# Build commands and execute all datasets in tmux window
tmux send-keys -t srbench:dsr "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:dsr "conda activate srbench" C-m
tmux send-keys -t srbench:dsr "echo 'Starting DSRRegressor on ENB COOLING dataset...'" C-m
tmux send-keys -t srbench:dsr "python analyze.py ../data/enb_cooling/enb_cooling.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../data/enb_cooling/enb_cooling_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr "echo 'Starting DSRRegressor on ENB HEATING dataset...'" C-m
tmux send-keys -t srbench:dsr "python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../data/enb_heating/enb_heating_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr "echo 'Starting DSRRegressor on AGRICULTURE SUSTAINABILITY dataset...'" C-m
tmux send-keys -t srbench:dsr "python analyze.py ../data/agric_sustainability/agric_sustainability.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../data/agric_sustainability/agric_sustainability_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr "echo 'Starting DSRRegressor on AGRICULTURE CONSUMER_TREND dataset...'" C-m
tmux send-keys -t srbench:dsr "python analyze.py ../data/agric_consumer_trend/agric_consumer_trend.tsv.gz --local -n_trials 10 -results ../.results -time_limit 48:00 -ml tuned.DSRRegressor -n_jobs 16 > ../data/agric_consumer_trend/agric_consumer_trend_DSR.log 2>&1 &" C-m
tmux send-keys -t srbench:dsr "echo 'All DSRRegressor experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:dsr "wait" C-m
tmux send-keys -t srbench:dsr "echo 'DSRRegressor experiments completed'" C-m

echo "DSRRegressor experiments started in tmux session 'srbench', window 'dsr'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:dsr"
