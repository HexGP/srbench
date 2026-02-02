#!/bin/bash
# Commands to run BSR on ENB datasets with SRBench

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing bsr windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' bsr$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for BSR experiments
tmux new-window -t srbench -n bsr -d
sleep 1  # Give tmux time to create the window

# Build commands and execute both datasets in tmux window
tmux send-keys -t srbench:bsr "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:bsr "conda activate srbench" C-m
tmux send-keys -t srbench:bsr "echo 'Starting BSR on COOLING dataset...'" C-m
tmux send-keys -t srbench:bsr "python analyze.py ../data/enb_cooling/enb_cooling.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.BSRRegressor -n_jobs 16 > ../data/enb_cooling/enb_cooling_BSR.log 2>&1 &" C-m
tmux send-keys -t srbench:bsr "echo 'Starting BSR on HEATING dataset...'" C-m
tmux send-keys -t srbench:bsr "python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.BSRRegressor -n_jobs 16 > ../data/enb_heating/enb_heating_BSR.log 2>&1 &" C-m
tmux send-keys -t srbench:bsr "echo 'Both BSR experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:bsr "wait" C-m
tmux send-keys -t srbench:bsr "echo 'BSR experiments completed'" C-m

echo "BSR experiments started in tmux session 'srbench', window 'bsr'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:bsr"
