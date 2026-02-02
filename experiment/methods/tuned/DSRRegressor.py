from ..DSRRegressor import DSRRegressor, complexity, model, base_config
import copy
from .params._dsrregressor import params

# DSO config structure - double the evals
dsr_config = base_config.copy()
dsr_config['training']['n_samples'] = 1000000  # double the evals

# Apply params if available
if 'params' in globals() and params:
    # Merge params into config
    for key, value in params.items():
        if key in dsr_config:
            if isinstance(dsr_config[key], dict) and isinstance(value, dict):
                dsr_config[key].update(value)
            else:
                dsr_config[key] = value

# Set max_time to 8 hours (matching paper standard)
dsr_config['max_time'] = 8 * 60 * 60

# Create the model using the bridge
est = DSRRegressor(dsr_config)

