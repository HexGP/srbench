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

# Path to the aifeynman_env Python
AIFEYNMAN_PYTHON = "/raid/hussein/miniconda3/envs/aifeynman_env/bin/python"
AIFEYNMAN_SCRIPT = "/raid/hussein/project/srbench/experiment/methods/aifeynman_runner.py"

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
