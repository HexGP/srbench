#!/bin/bash
# Commands to run AI-Feynman on ENB and Agriculture datasets with SRBench
# Data split: 80/20 train/test (SRBench uses 75/25 internally, but random_state ensures reproducibility)
# Random state: Uses SRBench's seed list (seeds.py) for consistency

# Create tmux session if it doesn't exist
if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

# Kill any existing aifeynman windows to avoid conflicts
tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' aifeynman$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

# Create new window for AI-Feynman experiments
tmux new-window -t srbench -n aifeynman -d
sleep 1  # Give tmux time to create the window

# Build commands and execute all datasets in tmux window
tmux send-keys -t srbench:aifeynman "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:aifeynman "conda activate srbench" C-m
tmux send-keys -t srbench:aifeynman "echo 'Starting AI-Feynman on ENB COOLING dataset...'" C-m
tmux send-keys -t srbench:aifeynman "python analyze.py ../data/enb_cooling/enb_cooling.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/enb_cooling/enb_cooling_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman "echo 'Starting AI-Feynman on ENB HEATING dataset...'" C-m
tmux send-keys -t srbench:aifeynman "python analyze.py ../data/enb_heating/enb_heating.tsv.gz --local -n_trials 10 -results ../results_enb -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/enb_heating/enb_heating_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman "echo 'Starting AI-Feynman on AGRICULTURE SUSTAINABILITY dataset...'" C-m
tmux send-keys -t srbench:aifeynman "python analyze.py ../data/agric_sustainability/agric_sustainability.tsv.gz --local -n_trials 10 -results ../results_agric -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/agric_sustainability/agric_sustainability_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman "echo 'Starting AI-Feynman on AGRICULTURE CONSUMER_TREND dataset...'" C-m
tmux send-keys -t srbench:aifeynman "python analyze.py ../data/agric_consumer_trend/agric_consumer_trend.tsv.gz --local -n_trials 10 -results ../results_agric -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/agric_consumer_trend/agric_consumer_trend_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman "echo 'All AI-Feynman experiments started. Waiting for completion...'" C-m
tmux send-keys -t srbench:aifeynman "wait" C-m
tmux send-keys -t srbench:aifeynman "echo 'AI-Feynman experiments completed'" C-m

echo "AI-Feynman experiments started in tmux session 'srbench', window 'aifeynman'"
echo "Attach with: tmux attach-session -t srbench"
echo "View window with: tmux select-window -t srbench:aifeynman"
