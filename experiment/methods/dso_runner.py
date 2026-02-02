"""
DSO runner script that runs in dso_env (Python 3.7).
Called by dso_bridge.py from srbench environment.
"""
import argparse
import json
import numpy as np
import sys
import os

# Add DSO to path
dsr_path = '/raid/hussein/project/z_file/DSR/dso'
if dsr_path not in sys.path:
    sys.path.insert(0, dsr_path)

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
        
        # Extract model
        if hasattr(regressor, 'program_') and regressor.program_ is not None:
            # Get the program string representation
            program = regressor.program_
            # Try to get symbolic expression if available
            try:
                model_str = str(program)
                # If it's a traversal, try to get the expression
                if hasattr(program, 'traversal'):
                    model_str = str(program.traversal)
                elif hasattr(program, 'sympy_expr'):
                    model_str = str(program.sympy_expr)
            except:
                model_str = str(program)
            complexity = len(model_str)
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
