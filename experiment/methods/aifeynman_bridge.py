"""
Bridge script to run AI-Feynman from Python 3.9 environment via subprocess.
This allows AI-Feynman to run in srbench (Python 3.11) environment.
"""
import subprocess
import sys
import os
import json
import tempfile
import numpy as np

# Detect aifeynman_env Python path - prefer environment variable, then common locations
# Try env_alfey first (matches z_codes), then aifeynman_env
_AIFEYNMAN_ENV_PYTHON = os.environ.get("AIFEYNMAN_PYTHON")
if not _AIFEYNMAN_ENV_PYTHON:
    # Try common conda locations
    for env_name in ["env_alfey", "aifeynman_env"]:
        for base in ["/raid/hussein/miniconda3/envs", "/home/hussein/miniconda3/envs",
                     os.path.expanduser("~/miniconda3/envs"), os.path.expanduser("~/anaconda3/envs")]:
            candidate = os.path.join(base, env_name, "bin", "python")
            if os.path.exists(candidate):
                _AIFEYNMAN_ENV_PYTHON = candidate
                break
        if _AIFEYNMAN_ENV_PYTHON:
            break
    # Fallback to hardcoded if nothing found
    if not _AIFEYNMAN_ENV_PYTHON:
        _AIFEYNMAN_ENV_PYTHON = "/raid/hussein/miniconda3/envs/aifeynman_env/bin/python"

AIFEYNMAN_PYTHON = _AIFEYNMAN_ENV_PYTHON
# Use relative path from this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AIFEYNMAN_SCRIPT = os.path.join(_BASE_DIR, "aifeynman_runner.py")

def run_aifeynman_fit(X, y, config):
    """
    Run AI-Feynman fit via subprocess bridge.
    
    Parameters
    ----------
    X : array-like
        Training features
    y : array-like
        Training targets
    config : dict
        AI-Feynman configuration (BF_try_time, BF_ops_file_type, polyfit_deg, 
        NN_epochs, random_state, test_percentage)
        
    Returns
    -------
    result : dict
        Contains 'model' (string) and 'complexity' (int)
    """
    # Create temporary files for data exchange
    with tempfile.TemporaryDirectory() as tmpdir:
        X_file = os.path.join(tmpdir, 'X.npy')
        y_file = os.path.join(tmpdir, 'y.npy')
        config_file = os.path.join(tmpdir, 'config.json')
        result_file = os.path.join(tmpdir, 'result.json')
        
        # Save data
        np.save(X_file, X)
        np.save(y_file, y)
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Run AI-Feynman in aifeynman_env
        cmd = [
            AIFEYNMAN_PYTHON,
            AIFEYNMAN_SCRIPT,
            '--X', X_file,
            '--y', y_file,
            '--config', config_file,
            '--output', result_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=_BASE_DIR,  # Set working directory
                capture_output=True,
                text=True,
                timeout=config.get('max_time', 7200),
                check=False
            )
            
            if result.returncode != 0:
                error_msg = f"AI-Feynman subprocess error (returncode {result.returncode}):\n{result.stderr}\n{result.stdout}"
                print(error_msg, file=sys.stderr)
                return {'model': 'x0', 'complexity': 0}
            
            # Also check stderr for warnings/errors even if returncode is 0
            if result.stderr and ('error' in result.stderr.lower() or 'exception' in result.stderr.lower()):
                print(f"AI-Feynman subprocess warning/error in stderr:\n{result.stderr}", file=sys.stderr)
            
            # Read result
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    return json.load(f)
            else:
                return {'model': 'x0', 'complexity': 0}
                
        except subprocess.TimeoutExpired:
            print("AI-Feynman subprocess timed out", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
        except Exception as e:
            print(f"AI-Feynman subprocess exception: {e}", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
