"""
Bridge script to run DSO from Python 3.7 environment via subprocess.
This allows DSO to run in srbench (Python 3.11) environment.
Matches z_codes/dso_bridge.py behavior.
"""
import subprocess
import sys
import os
import json
import tempfile
import numpy as np
import pickle
from pathlib import Path

# Detect dso_env Python path - prefer environment variable, then common locations
_DSO_ENV_PYTHON = os.environ.get("DSO_PYTHON")
if not _DSO_ENV_PYTHON:
    # Try common conda locations
    for base in ["/raid/hussein/miniconda3/envs", "/home/hussein/miniconda3/envs", 
                 os.path.expanduser("~/miniconda3/envs"), os.path.expanduser("~/anaconda3/envs")]:
        candidate = os.path.join(base, "dso_env", "bin", "python")
        if os.path.exists(candidate):
            _DSO_ENV_PYTHON = candidate
            break
    # Fallback to hardcoded if nothing found
    if not _DSO_ENV_PYTHON:
        _DSO_ENV_PYTHON = "/raid/hussein/miniconda3/envs/dso_env/bin/python"

DSO_PYTHON = _DSO_ENV_PYTHON
# Use relative path from this file (matches z_codes approach)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DSO_SCRIPT = os.path.join(_BASE_DIR, "dso_runner.py")

def run_dso_fit(X, y, config):
    """
    Run DSO fit via subprocess bridge.
    
    Parameters
    ----------
    X : array-like
        Training features
    y : array-like
        Training targets
    config : dict
        DSO configuration
        
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
        
        # Run DSO in dso_env
        # Set environment variable for protobuf compatibility
        env = os.environ.copy()
        env['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
        
        # Set DSR_PATH in environment so dso_runner.py can find DSO code
        # Prefer z_codes/DSR/dso if available (matches z_codes behavior)
        _srbench_root = os.path.normpath(os.path.join(_BASE_DIR, "..", ".."))
        _z_codes_dsr = os.path.join(_srbench_root, "..", "z_codes", "DSR", "dso")
        if os.path.isdir(_z_codes_dsr):
            env["DSR_PATH"] = os.path.abspath(_z_codes_dsr)
        elif "DSR_PATH" not in env:
            # Fallback to srbench/z_codes/DSR/dso
            _srbench_z_codes_dsr = os.path.join(_srbench_root, "z_codes", "DSR", "dso")
            if os.path.isdir(_srbench_z_codes_dsr):
                env["DSR_PATH"] = os.path.abspath(_srbench_z_codes_dsr)
        
        cmd = [
            DSO_PYTHON,
            DSO_SCRIPT,
            '--X', X_file,
            '--y', y_file,
            '--config', config_file,
            '--output', result_file
        ]
        
        try:
            # Don't capture stdout/stderr so DSO training iteration output streams to the log (like srbench)
            result = subprocess.run(
                cmd,
                cwd=_BASE_DIR,  # Set working directory like z_codes
                capture_output=False,
                text=True,
                timeout=config.get('max_time', 3600),
                check=False,
                env=env
            )
            
            if result.returncode != 0:
                print(f"DSO subprocess error (returncode {result.returncode})", file=sys.stderr)
                return {'model': 'x0', 'complexity': 0}
            
            # Read result
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    return json.load(f)
            else:
                return {'model': 'x0', 'complexity': 0}
                
        except subprocess.TimeoutExpired:
            print("raising TimeOutException", flush=True)
            print("DSO subprocess timed out", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
        except Exception as e:
            print(f"DSO subprocess exception: {e}", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
