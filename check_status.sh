#!/bin/bash
# Quick status check for SRBench experiments

echo "=== Process Status ==="
ps aux | grep -E "analyze.py|python.*analyze" | grep -v grep || echo "No analyze.py processes running"

echo ""
echo "=== Expected Jobs ==="
echo "BSR: 10 trials × 2 datasets = 20 jobs"
echo "AI-Feynman: 10 trials × 2 datasets = 20 jobs"
echo "DSR: 10 trials × 2 datasets = 20 jobs"
echo "Total expected: 60 result files"

echo ""
echo "=== Current Results ==="
total_results=$(find /raid/hussein/project/srbench/results_enb -name "*.json" 2>/dev/null | wc -l)
echo "Found: $total_results result files"

echo ""
echo "=== Results by Dataset ==="
for dataset in enb_cooling enb_heating; do
    for method in tuned.BSRRegressor tuned.AIFeynman tuned.DSRRegressor; do
        count=$(find /raid/hussein/project/srbench/results_enb/$dataset -name "*${method}*.json" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            echo "$dataset/$method: $count/10 completed"
        fi
    done
done

echo ""
echo "=== Log Files (last 3 lines) ==="
for log in /raid/hussein/project/srbench/data/enb_*/enb_*.log; do
    if [ -f "$log" ]; then
        echo "--- $(basename $log) ---"
        tail -3 "$log"
        echo ""
    fi
done
