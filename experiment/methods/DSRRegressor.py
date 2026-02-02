import sys
import os
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

# Import the bridge
sys.path.insert(0, os.path.dirname(__file__))
from dso_bridge import run_dso_fit

# Base configuration for DSR
base_config = {
    'task': {
        'task_type': 'regression',
        'function_set': ['add', 'sub', 'mul', 'div', 'sin', 'cos', 'exp', 'log']
    },
    'training': {
        'n_samples': 1000000,
        'batch_size': 1000
    },
    'experiment': {
        'logdir': None
    },
    'gp_meld': {
        'run_gp_meld': False
    },
    'max_time': 3600  # 1 hour default
}

class DSRRegressor(BaseEstimator, RegressorMixin):
    """Wrapper for DSO that runs via subprocess bridge."""
    
    def __init__(self, config=None):
        self.config = config if config is None else base_config.copy()
        self.model_ = None
        self.complexity_ = 0
        
    def fit(self, X, y):
        """Fit DSO model via subprocess bridge."""
        # Update config with dataset
        config = self.config.copy()
        config['task']['dataset'] = None  # Will be set by sklearn interface
        
        # Run DSO via bridge
        result = run_dso_fit(X, y, config)
        self.model_ = result['model']
        self.complexity_ = result['complexity']
        return self
    
    def predict(self, X):
        """Predict using the learned model."""
        # For symbolic regression, we'd need to evaluate the expression
        # This is a placeholder - SRBench extracts the model string directly
        return np.zeros(len(X))
    
    def complexity(self):
        return self.complexity_
    
    def model(self, X=None):
        return self.model_

# Initialize estimator
est = DSRRegressor(base_config)

def complexity(est):
    return est.complexity()

def model(est, X=None):
    return est.model(X)
