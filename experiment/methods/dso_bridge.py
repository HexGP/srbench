"""
Bridge script to run DSO from Python 3.7 environment via subprocess.
This allows DSO to run in srbench (Python 3.11) environment.
"""
import subprocess
import sys
import os
import json
import tempfile
import numpy as np
import pickle
from pathlib import Path

# Path to the dso_env Python
DSO_PYTHON = "/raid/hussein/miniconda3/envs/dso_env/bin/python"
DSO_SCRIPT = "/raid/hussein/project/srbench/experiment/methods/dso_runner.py"

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
        
        cmd = [
            DSO_PYTHON,
            DSO_SCRIPT,
            '--X', X_file,
            '--y', y_file,
            '--config', config_file,
            '--output', result_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.get('max_time', 3600),
                check=False,
                env=env
            )
            
            if result.returncode != 0:
                error_msg = f"DSO subprocess error (returncode {result.returncode}):\n{result.stderr}\n{result.stdout}"
                print(error_msg, file=sys.stderr)
                return {'model': 'x0', 'complexity': 0}
            
            # Also check stderr for warnings/errors even if returncode is 0
            if result.stderr and ('error' in result.stderr.lower() or 'exception' in result.stderr.lower()):
                print(f"DSO subprocess warning/error in stderr:\n{result.stderr}", file=sys.stderr)
            
            # Read result
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    return json.load(f)
            else:
                return {'model': 'x0', 'complexity': 0}
                
        except subprocess.TimeoutExpired:
            print("DSO subprocess timed out", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
        except Exception as e:
            print(f"DSO subprocess exception: {e}", file=sys.stderr)
            return {'model': 'x0', 'complexity': 0}
