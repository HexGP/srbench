# Why agric_01_sustainability_DSR Shows x0 Despite Finding Equations

## What happens in the log

- **During training**: DSO prints "New best" with real equations.
- **Final result**: Saved model is always `"symbolic_model": "x0"` and `time_time` is ~3600 s.

So equations are found during the run but the saved model is the fallback x0.

## Cause

1. **Time limit**: The run was stopped at **3600 seconds (1 hour)** by either the bridge subprocess timeout or the evaluate_model alarm.
2. **No graceful stop in DSO**: DSO only stopped when `nevals >= n_samples`. It did not check wall-clock time. When the 1-hour limit was hit, the subprocess was killed before DSO could finish and write the best program. The bridge then returned the fallback `{"model": "x0"}`.

So the equations you see are the best found during training; they are lost when the process is killed.

## Fix applied (no time increase)

The time limit is unchanged (3600 s or 36000 s by dataset size). The only change is in DSO:

- **DSO train.py**: Trainer now accepts `max_time` and checks wall time each iteration. When the limit is reached, it sets `done = True` so the loop exits, `finish()` runs, and the best program is returned and written by dso_runner.
- **DSO core.py**: `make_trainer()` passes `max_time` from config into the Trainer.

So when the **same** time limit is reached, DSO stops gracefully and the best equation found so far is saved instead of the process being killed and x0 returned.
