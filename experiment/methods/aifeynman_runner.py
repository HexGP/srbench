"""
AI-Feynman runner script that runs in aifeynman_env (Python 3.9).
Called by aifeynman_bridge.py from srbench environment.
"""
import argparse
import json
import numpy as np
import sys
import os
import tempfile

# Add AI-Feynman to path
aifeynman_path = '/raid/hussein/project/srbench/z_codes/AI-Feynman'
if aifeynman_path not in sys.path:
    sys.path.insert(0, aifeynman_path)

# Import AI-Feynman
from aifeynman import run_aifeynman

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
    
    # Create temporary directory for AI-Feynman
    temp_dir = tempfile.mkdtemp(prefix='aifeynman_')
    filename = 'data'
    data_file = os.path.join(temp_dir, filename)
    
    # Combine X and y into single array (AI-Feynman expects last column as target)
    data = np.column_stack([X, y])
    np.savetxt(data_file, data)
    
    # Save current working directory
    original_cwd = os.getcwd()
    
    try:
        # Change to temp directory (AI-Feynman saves results relative to current directory)
        os.chdir(temp_dir)
        
        # Set random seed if provided
        if config.get('random_state') is not None:
            np.random.seed(config['random_state'])
        
        # Run AI-Feynman
        run_aifeynman(
            pathdir='./',
            filename=filename,
            BF_try_time=config.get('BF_try_time', 60),
            BF_ops_file_type=config.get('BF_ops_file_type', '14ops.txt'),
            polyfit_deg=config.get('polyfit_deg', 4),
            NN_epochs=config.get('NN_epochs', 4000),
            vars_name=[],
            test_percentage=config.get('test_percentage', 20)
        )
        
        # Extract best model from results
        results_file = os.path.join(temp_dir, 'results', f'solution_{filename}')
        
        if os.path.exists(results_file):
            try:
                # Load results - format: [test_error, log_err, log_err_all, complexity, error, equation]
                # Or without test: [log_err, log_err_all, complexity, error, equation]
                results = np.loadtxt(results_file, dtype=str, ndmin=2)
                if len(results) > 0 and results.size > 0:
                    # Get the best model (first row, last column is the equation)
                    if results.ndim == 1:
                        equation = str(results[-1])
                    else:
                        equation = str(results[0, -1])
                    
                    # Compute complexity
                    try:
                        from sympy import Symbol, preorder_traversal
                        from sympy.parsing.sympy_parser import parse_expr
                        n_features = X.shape[1]
                        local_dict = {f'x{i}': Symbol(f'x{i}') for i in range(n_features)}
                        model_sym = parse_expr(equation, local_dict=local_dict)
                        complexity = sum(1 for _ in preorder_traversal(model_sym))
                    except:
                        complexity = len(equation)
                else:
                    equation = "x0"
                    complexity = 0
            except Exception as e:
                print(f"Error reading results file: {e}", file=sys.stderr)
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
                equation = "x0"
                complexity = 0
        else:
            print(f"Results file not found: {results_file}", file=sys.stderr)
            equation = "x0"
            complexity = 0
        
        # Save result
        result = {
            'model': equation,
            'complexity': int(complexity)
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f)
            
    except Exception as e:
        import traceback
        error_msg = f"AI-Feynman fit error: {e}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        result = {'model': 'x0', 'complexity': 0}
        with open(args.output, 'w') as f:
            json.dump(result, f)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    main()
