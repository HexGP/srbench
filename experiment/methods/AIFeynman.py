import os
import sys
import numpy as np
import tempfile
import shutil
from sklearn.base import BaseEstimator, RegressorMixin

# Add AI-Feynman to path if needed
aifeynman_path = '/raid/hussein/project/z_file/AI-Feynman'
if aifeynman_path not in sys.path:
    sys.path.insert(0, aifeynman_path)

from aifeynman import run_aifeynman

class AIFeynmanRegressor(BaseEstimator, RegressorMixin):
    """Wrapper for AI-Feynman to make it scikit-learn compatible"""
    
    def __init__(self, BF_ops_file_type='14ops.txt', BF_try_time=60, 
                 NN_epochs=4000, max_time=7200, polyfit_deg=4, 
                 random_state=None, test_percentage=20):
        self.BF_ops_file_type = BF_ops_file_type
        self.BF_try_time = BF_try_time
        self.NN_epochs = NN_epochs
        self.max_time = max_time
        self.polyfit_deg = polyfit_deg
        self.random_state = random_state
        self.test_percentage = test_percentage
        self.model_ = None
        self.complexity_ = None
        self.temp_dir = None
        self.filename = None
        
    def fit(self, X, y):
        """Fit AI-Feynman on training data"""
        # Create temporary directory for AI-Feynman files
        self.temp_dir = tempfile.mkdtemp(prefix='aifeynman_')
        self.filename = 'data'
        
        # Combine X and y into single array (AI-Feynman expects last column as target)
        data = np.column_stack([X, y])
        data_file = os.path.join(self.temp_dir, self.filename)
        np.savetxt(data_file, data)
        
        # Set random seed if provided
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        # Save current working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory (AI-Feynman saves results relative to current directory)
            os.chdir(self.temp_dir)
            
            # Run AI-Feynman
            run_aifeynman(
                pathdir='./',
                filename=self.filename,
                BF_try_time=self.BF_try_time,
                BF_ops_file_type=self.BF_ops_file_type,
                polyfit_deg=self.polyfit_deg,
                NN_epochs=self.NN_epochs,
                vars_name=[],
                test_percentage=self.test_percentage
            )
            
            # Extract best model from results
            # AI-Feynman saves results in results/solution_{filename} relative to current directory
            results_file = os.path.join(self.temp_dir, 'results', f'solution_{self.filename}')
            
            if os.path.exists(results_file):
                try:
                    # Load results - format: [test_error, log_err, log_err_all, complexity, error, equation]
                    # Or without test: [log_err, log_err_all, complexity, error, equation]
                    results = np.loadtxt(results_file, dtype=str, ndmin=2)
                    if len(results) > 0 and results.size > 0:
                        # Get the best model (first row, last column is the equation)
                        # Handle both 1D and 2D arrays
                        if results.ndim == 1:
                            equation = str(results[-1])
                        else:
                            equation = str(results[0, -1])
                        self.model_ = equation
                        # Use sympy to compute proper complexity
                        try:
                            from sympy import parse_expr, Symbol, preorder_traversal
                            from sympy.parsing.sympy_parser import parse_expr as parse_expr_parser
                            # Create local dict for parsing
                            n_features = X.shape[1]
                            local_dict = {f'x{i}': Symbol(f'x{i}') for i in range(n_features)}
                            model_sym = parse_expr_parser(self.model_, local_dict=local_dict)
                            self.complexity_ = sum(1 for _ in preorder_traversal(model_sym))
                        except:
                            # Fallback: use string length
                            self.complexity_ = len(self.model_)
                    else:
                        self.model_ = "x0"
                        self.complexity_ = 1
                except Exception as e:
                    print(f"Error reading results file: {e}", file=sys.stderr)
                    import traceback
                    print(traceback.format_exc(), file=sys.stderr)
                    self.model_ = "x0"
                    self.complexity_ = 1
            else:
                print(f"Results file not found: {results_file}", file=sys.stderr)
                # List what files exist in results directory
                results_dir = os.path.join(self.temp_dir, 'results')
                if os.path.exists(results_dir):
                    print(f"Files in results directory: {os.listdir(results_dir)}", file=sys.stderr)
                self.model_ = "x0"
                self.complexity_ = 1
                
        except Exception as e:
            print(f"AI-Feynman error: {e}", file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            self.model_ = "x0"
            self.complexity_ = 1
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
        
        return self
    
    def predict(self, X):
        """Predict using the learned model"""
        if self.model_ is None:
            return np.zeros(len(X))
        
        # Simple evaluation - in practice, you'd parse the symbolic expression
        # For now, return zeros as placeholder
        # TODO: Implement proper symbolic evaluation
        return np.zeros(len(X))
    
    def complexity(self):
        """Return model complexity"""
        return self.complexity_ if self.complexity_ is not None else 0
    
    def model(self):
        """Return the symbolic model"""
        return self.model_ if self.model_ is not None else "x0"
    
    def __del__(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

# Initialize estimator
est = AIFeynmanRegressor(
    BF_ops_file_type='14ops.txt',
    BF_try_time=60,
    NN_epochs=4000,
    max_time=7200,
    polyfit_deg=4,
    random_state=11284,
    test_percentage=20
)

def complexity(est):
    return est.complexity()

def model(est, X=None):
    return est.model()
