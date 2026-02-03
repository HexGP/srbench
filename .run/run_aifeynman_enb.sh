#!/bin/bash
# Commands to run AI-Feynman on ENB datasets with SRBench
# Data split: 80/20 train/test (SRBench uses 80/20 split internally, random_state ensures reproducibility)
# Random state: Uses SRBench's seed list (seeds.py) for consistency

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing aifeynman_enb windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' aifeynman_enb$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for AI-Feynman ENB experiments
tmux new-window -t srbench -n aifeynman_enb -d
sleep 1  # Give tmux time to create the window

# Build commands and execute ENB datasets in tmux window
tmux send-keys -t srbench:aifeynman_enb "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:aifeynman_enb "conda activate srbench" C-m
tmux send-keys -t srbench:aifeynman_enb "echo 'Starting AI-Feynman on ENB COOLING dataset...'" C-m
tmux send-keys -t srbench:aifeynman_enb "python analyze.py ../data/enb_cooling/enb_cooling.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/enb_cooling/enb_cooling_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman_enb "echo 'Starting AI-Feynman on ENB HEATING dataset...'" C-m
tmux send-keys -t srbench:aifeynman_enb "python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/enb_heating/enb_heating_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman_enb "echo 'All ENB AI-Feynman experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:aifeynman_enb "wait" C-m
tmux send-keys -t srbench:aifeynman_enb "echo 'ENB AI-Feynman experiments completed'" C-m

echo "AI-Feynman ENB experiments started in tmux session 'srbench', window 'aifeynman_enb'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:aifeynman_enb"
