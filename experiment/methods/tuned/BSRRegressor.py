from ..BSRRegressor import complexity,model,est
from .params._bsrregressor import params

# Only set valid parameters
valid_params = {k: v for k, v in params.items() if k in ['alpha1', 'alpha2', 'beta', 'disp', 'itrNum', 'treeNum', 'val']}
if valid_params:
    for key, value in valid_params.items():
        if hasattr(est, key):
            setattr(est, key, value)

est.max_time = 8*60*60
# double the evals
est.itrNum = int(est.itrNum*2**0.5)
est.val = int(est.val*2**0.5)
