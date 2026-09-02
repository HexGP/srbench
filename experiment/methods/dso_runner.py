"""
DSO runner script that runs in dso_env (Python 3.7).
Called by dso_bridge.py from srbench environment.
"""
import argparse
import json
import numpy as np
import sys
import os

# Add DSO to path: prefer DSR_PATH (matches z_codes/dso_runner.py)
_ZCODES = os.path.dirname(os.path.abspath(__file__))
# Try DSR_PATH first (set by dso_bridge.py)
dsr_path = os.environ.get("DSR_PATH")
if dsr_path and os.path.isdir(dsr_path):
    dsr_path = os.path.abspath(dsr_path)
    if dsr_path not in sys.path:
        sys.path.insert(0, dsr_path)
else:
    # Fallback: try relative to this file (srbench/z_codes/DSR/dso)
    _default_dsr = os.path.join(_ZCODES, "..", "..", "z_codes", "DSR", "dso")
    _default_dsr = os.path.abspath(_default_dsr)
    if os.path.isdir(_default_dsr) and _default_dsr not in sys.path:
        sys.path.insert(0, _default_dsr)
    else:
        # Try parent z_codes (when run from z_codes directly)
        _parent_z_codes = os.path.join(_ZCODES, "..", "..", "..", "z_codes", "DSR", "dso")
        _parent_z_codes = os.path.abspath(_parent_z_codes)
        if os.path.isdir(_parent_z_codes) and _parent_z_codes not in sys.path:
            sys.path.insert(0, _parent_z_codes)

# Import DSO - use sklearn interface directly
from dso.task.regression.sklearn import DeepSymbolicRegressor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--X', required=True, help='Path to X.npy')
    parser.add_argument('--y', required=True, help='Path to y.npy')
    parser.add_argument('--config', required=True, help='Path to config.json')
    parser.add_argument('--output', required=True, help='Path to output result.json')
    
    args = parser.parse_args()
    
    # Load data
    X = np.load(args.X)
    y = np.load(args.y)
    
    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Ensure required config fields exist (DSO will merge with defaults, but some fields are required)
    if 'experiment' not in config:
        config['experiment'] = {}
    if 'logdir' not in config['experiment']:
        config['experiment']['logdir'] = None
    
    if 'gp_meld' not in config:
        config['gp_meld'] = {}
    if 'run_gp_meld' not in config['gp_meld']:
        config['gp_meld']['run_gp_meld'] = False
    
    # Create and fit DSO
    try:
        regressor = DeepSymbolicRegressor(config)
        regressor.fit(X, y)
        
        # Extract model - prefer sympy_expr so SRBench can evaluate equation-on-test metrics
        if hasattr(regressor, 'program_') and regressor.program_ is not None:
            program = regressor.program_
            try:
                if hasattr(program, 'sympy_expr'):
                    model_str = str(program.sympy_expr)
                elif hasattr(program, 'traversal'):
                    model_str = str(program.traversal)
                else:
                    model_str = str(program)
            except Exception:
                model_str = str(program)
            complexity = len(str(model_str))
        else:
            model_str = "x0"
            complexity = 0
        
        # Save result
        result = {
            'model': model_str,
            'complexity': complexity
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f)
            
    except Exception as e:
        import traceback
        error_msg = f"DSO fit error: {e}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        result = {'model': 'x0', 'complexity': 0}
        with open(args.output, 'w') as f:
            json.dump(result, f)

if __name__ == '__main__':
    main()
