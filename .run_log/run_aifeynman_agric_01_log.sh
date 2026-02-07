#!/bin/bash
# AIFeynman on Agriculture LOG (transformed targets) - 0.1 sample.
# Run csv_to_tsvgz_agric_log.py 0.1 first.

if ! tmux has-session -t srbench 2>/dev/null; then
    tmux new-session -d -s srbench
fi

tmux list-windows -t srbench -F '#{window_id} #{window_name}' 2>/dev/null | grep ' aifeynman_agric_01_log$' | awk '{print $1}' | xargs -r -I {} tmux kill-window -t {} 2>/dev/null

tmux new-window -t srbench -n aifeynman_agric_01_log -d
sleep 1

tmux send-keys -t srbench:aifeynman_agric_01_log "cd /raid/hussein/project/srbench/experiment" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "conda activate srbench" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "echo 'Starting AIFeynman on AGRICULTURE LOG (0.1) SUSTAINABILITY...'" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "python analyze.py ../data/agric_01_sustainability_log/agric_01_sustainability_log.tsv.gz --local -n_trials 10 -results ../results_agric_01_log -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/agric_01_sustainability_log/agric_01_sustainability_log_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "echo 'Starting AIFeynman on AGRICULTURE LOG (0.1) CONSUMER_TREND...'" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "python analyze.py ../data/agric_01_consumer_trend_log/agric_01_consumer_trend_log.tsv.gz --local -n_trials 10 -results ../results_agric_01_log -time_limit 48:00 -ml tuned.AIFeynman -n_jobs 16 > ../data/agric_01_consumer_trend_log/agric_01_consumer_trend_log_AIFeynman.log 2>&1 &" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "echo 'All Agriculture LOG (0.1) AIFeynman started. Waiting...'" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "wait" C-m
tmux send-keys -t srbench:aifeynman_agric_01_log "echo 'Agriculture LOG (0.1) AIFeynman completed'" C-m

echo "AIFeynman Agriculture LOG (0.1) started in tmux session 'srbench', window 'aifeynman_agric_01_log'"
