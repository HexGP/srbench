# Fixes Applied to Make SRBench Work Like z_codes

## Summary
Fixed srbench to actually find equations (not just "x0" fallbacks) by aligning it with z_codes behavior. All algorithms (DSR, BSR, AIFeynman) should now work correctly.

## Changes Made

### 1. DSR Fixes

#### `experiment/methods/dso_bridge.py`
- **Changed**: Hardcoded Python path → Dynamic detection with fallbacks
- **Changed**: Hardcoded script path → Relative path from file location
- **Added**: DSR_PATH environment variable setting (matches z_codes)
- **Added**: Working directory setting (`cwd=_BASE_DIR`) for subprocess
- **Result**: DSO can now find its code via DSR_PATH, matching z_codes behavior

#### `experiment/methods/dso_runner.py`
- **Changed**: Path resolution logic to match z_codes/dso_runner.py
- **Improved**: Better fallback path detection (tries multiple locations)
- **Result**: DSO runner can find DSO code whether run from srbench or z_codes

#### `experiment/evaluate_model.py`
- **Added**: DSR_PATH environment variable setting in `set_env_vars()`
- **Result**: DSR_PATH is set automatically when running experiments

#### `.run/run_dsr_enb.sh`
- **Added**: DSR_PATH export before running experiments
- **Result**: DSR_PATH is available in the shell environment

### 2. BSR Fixes

#### `.run/install_dependencies.sh`
- **Changed**: Hardcoded paths → Try multiple locations (`srbench/z_codes/BSR` and `z_codes/BSR`)
- **Result**: BSR installation works regardless of project structure

### 3. AIFeynman Fixes

#### `experiment/methods/aifeynman_bridge.py`
- **Changed**: Hardcoded Python path → Dynamic detection (tries `env_alfey` first, then `aifeynman_env`)
- **Changed**: Hardcoded script path → Relative path from file location
- **Added**: Working directory setting (`cwd=_BASE_DIR`) for subprocess
- **Result**: AIFeynman bridge matches z_codes environment detection

### 4. Environment Detection

All bridges now:
- Check environment variables first (`DSO_PYTHON`, `AIFEYNMAN_PYTHON`)
- Try common conda locations (`/raid/hussein/miniconda3/envs`, `~/miniconda3/envs`, etc.)
- Fall back to hardcoded paths only if nothing found
- Match z_codes behavior for consistency

## Verification Steps

1. **Install dependencies**:
   ```bash
   cd /raid/hussein/project/srbench
   bash .run/install_dependencies.sh
   ```

2. **Run DSR**:
   ```bash
   bash .run/run_dsr_enb.sh
   ```
   - Should find equations (not just "x0")
   - Check logs: `.logs/enb_heating_DSR.log`

3. **Run BSR**:
   ```bash
   bash .run/run_bsr_enb.sh
   ```
   - Should not have `ModuleNotFoundError: No module named 'bsr'`
   - Check logs: `.logs/enb_heating_BSR.log`

4. **Run AIFeynman**:
   ```bash
   bash .run/run_aifeynman_enb.sh
   ```
   - Should use correct Python environment
   - Check logs: `.logs/enb_heating_AIFeynman.log`

## Key Differences Fixed

| Issue | Before | After |
|-------|--------|-------|
| DSR finds code | Hardcoded paths, no DSR_PATH | DSR_PATH set, dynamic detection |
| BSR import | Only checks one location | Checks multiple locations |
| AIFeynman env | Hardcoded `aifeynman_env` | Tries `env_alfey` first (matches z_codes) |
| Working directory | Not set | Set to bridge script directory |
| Environment vars | Not set in evaluate_model | DSR_PATH set automatically |

## Notes

- All algorithms already had `max_time = 8 * 60 * 60` (8 hours) in tuned versions
- DSR_PATH is now set consistently across all entry points
- Path detection matches z_codes behavior for compatibility
- Install script handles both `srbench/z_codes/` and `z_codes/` locations
