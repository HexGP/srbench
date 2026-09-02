import numpy as np
from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
try:
    from sklearn.metrics import mean_absolute_percentage_error
except ImportError:
    mean_absolute_percentage_error = None

"""
Timeout handling
"""

MAXTIME = 60

import signal
class SimplifyTimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    print(f"raising SimplifyTimeOutException")
    raise SimplifyTimeOutException


"""
For all of these, higher is better
"""
def accuracy(est, X, y):
    pred = est.predict(X)

    mse = mean_squared_error(y, pred)
    y_var = np.var(y)
    if(y_var == 0.0):
        y_var = 1e-9

    r2 = 1 - mse / y_var
    r2 = np.round(r2, 3)
    return r2

"""
Utilities
"""


def round_floats(ex1):
    ex2 = ex1
    for a in sp.preorder_traversal(ex1):
        if isinstance(a, sp.Float):
            if abs(a) < 0.0001:
                ex2 = ex2.subs(a, sp.Integer(0))
            else:
                ex2 = ex2.subs(a, round(a, 3))
    return ex2



def get_symbolic_model(pred_model, local_dict):
    # TODO: update namespace for exact_formula runs
    sp_model = sp.parse_expr(pred_model, local_dict=local_dict)
    sp_model = round_floats(sp_model)

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(MAXTIME) # maximum time, defined above
    try:
        sp_model = sp.simplify(sp_model)
    except Exception as e:
        print('Warning: simplify failed. Msg:',e)
        pass
    return sp_model

def simplicity(pred_model, feature_names):
    local_dict = {f:sp.Symbol(f) for f in feature_names} 
    sp_model = get_symbolic_model(pred_model, local_dict)
    # compute num. components
    num_components = 0
    for _ in sp.preorder_traversal(sp_model):
        num_components += 1
    # compute simplicity as per juding criteria
    simplicity = -np.round(np.log(num_components)/np.log(5), 1)
    return simplicity


# Fallback model strings (timeout/failure) - interpret as "use first feature" for equation metrics
FALLBACK_MODELS = ("x0", "0", "nan")


def _equation_predictions_sympy(model_str, feature_names, X):
    """Evaluate a symbolic expression string on X using sympy. Returns 1d array or None."""
    if not isinstance(model_str, str) or not model_str or feature_names is None or len(feature_names) == 0:
        return None
    # Handle fallback models: use first feature as prediction so equation metrics are computed
    s = model_str.strip()
    if s.lower() in FALLBACK_MODELS:
        try:
            import pandas as pd
            if isinstance(X, pd.DataFrame):
                X_arr = X.values if hasattr(X, 'values') else np.asarray(X)
            else:
                X_arr = np.asarray(X)
            if X_arr.ndim == 1:
                X_arr = X_arr.reshape(-1, 1)
            if X_arr.shape[1] > 0 and X_arr.shape[0] > 0:
                return np.asarray(X_arr[:, 0], dtype=np.float64).flatten()
        except Exception:
            pass
        return None
    # Normalize: 1-based first (x1,X1 -> first feature; DSO's own convention for
    # ENB/Agric equations), then 0-based (x0,X0 -> first feature; AIFeynman
    # convention, and DSR's literal "x0" fallback). Word-boundary regex avoids
    # "x1" clobbering "x10".."x19" the way a plain substring .replace() would.
    import re as _re
    def _apply_index_sub(s, mapping):
        if not mapping:
            return s
        pattern = _re.compile(r'\b(' + '|'.join(_re.escape(k) for k in mapping) + r')\b')
        return pattern.sub(lambda m: mapping[m.group(0)], s)
    map1 = {}
    for i, f in enumerate(feature_names):
        map1["x" + str(i + 1)] = f
        map1["X" + str(i + 1)] = f
    s = _apply_index_sub(s, map1)
    map0 = {}
    for i, f in enumerate(feature_names):
        map0["x" + str(i)] = f
        map0["X" + str(i)] = f
    s = _apply_index_sub(s, map0)
    def _sub_sym(a, b):
        return sp.Add(a, -b)
    def _div_sym(a, b):
        return sp.Mul(a, sp.Pow(b, -1))
    local_dict = {f: sp.Symbol(f) for f in feature_names}
    local_dict.update({
        "add": sp.Add, "mul": sp.Mul, "sub": _sub_sym, "div": _div_sym,
        "exp": sp.exp, "log": sp.log, "sin": sp.sin, "cos": sp.cos,
        "sqrt": sp.sqrt, "abs": sp.Abs, "neg": lambda x: -x,
        "inv": lambda x: 1 / x, "square": lambda x: x**2,
        "cube": lambda x: x**3, "quart": lambda x: x**4,
    })
    try:
        expr = parse_expr(s, local_dict=local_dict)
    except Exception:
        return None
    try:
        func = sp.lambdify(feature_names, expr, modules=["numpy"])
    except Exception:
        return None
    try:
        import pandas as pd
        if isinstance(X, pd.DataFrame):
            X_arr = X[feature_names].values if all(c in X.columns for c in feature_names) else np.asarray(X)
        else:
            X_arr = np.asarray(X)
    except Exception:
        X_arr = np.asarray(X)
    if X_arr.ndim == 1:
        X_arr = X_arr.reshape(-1, 1)
    if X_arr.shape[1] != len(feature_names):
        return None
    try:
        y_pred = func(*[X_arr[:, j] for j in range(len(feature_names))])
        y_pred = np.asarray(y_pred, dtype=np.float64).flatten()
        if y_pred.shape[0] != X_arr.shape[0]:
            return None
        return y_pred
    except Exception:
        return None


def equation_predictions(model_str, feature_names, X, est=None, est_name=""):
    """
    Get predictions by evaluating the learned equation on X (same as @codes).
    For BSR, uses est.predict(X). Otherwise tries to parse model_str with sympy and evaluate.
    Returns 1d array of shape (n_samples,) or None if evaluation fails.
    """
    if est is not None and "BSR" in est_name:
        try:
            y = est.predict(X)
            return np.asarray(y).flatten()
        except Exception:
            pass
    # Handle model_str stored as list (e.g. DSR traversal from JSON) - treat as fallback
    if isinstance(model_str, (list, tuple)):
        model_str = "x0"
    return _equation_predictions_sympy(model_str, feature_names, X)


def equation_metrics(y_true, y_pred):
    """
    Compute MSE, MAE, RMSE, MAPE for equation-on-data (like @codes symbolic_model_metrics).
    y_true, y_pred must be in the same space (e.g. log(y) for agric, raw for enb).
    Returns dict with equation_mse, equation_mae, equation_rmse, equation_mape (mape can be None).
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return None
    mse = float(mean_squared_error(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mape = None
    if mean_absolute_percentage_error is not None:
        try:
            m = mean_absolute_percentage_error(y_true, y_pred)
            mape = float(m) if np.isfinite(m) else None
        except Exception:
            pass
    return {"equation_mse": mse, "equation_mae": mae, "equation_rmse": rmse, "equation_mape": mape}

"""
Problem specific
"""
def symbolic_equivalence(true_model, pred_model, local_dict):
    """Check whether symbolic model is equivalent to the ground truth model."""
    sp_model = get_symbolic_model(pred_model, local_dict)

    sym_diff = round_floats(true_model - sp_model)
    sym_frac = round_floats(sp_model/true_model)
    print('true_model:',true_model, '; \npred_model:',sp_model)

    try:
        diff_const=sym_diff.is_constant(simplify=False) 
        frac_const=sym_frac.is_constant(simplify=False) 

        # check if we can skip simplification
        if not diff_const and not frac_const:
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(MAXTIME) # maximum time, defined above
            try:
                if not diff_const:
                    sym_diff = sp.simplify(sym_diff)
                    diff_const=sym_diff.is_constant() 
                if not frac_const:
                    sym_frac = sp.simplify(sym_frac)
                    frac_const=sym_frac.is_constant() 
            except Exception as e:
                print('Warning: simplify failed. Msg:',e)
                pass
    except Exception as e:
        print('const checking failed.')
        diff_const=False
        frac_const=False
        pass


    result = dict(
            equivalent = (
                str(sym_diff) == '0'
                or diff_const 
                or frac_const
            ),
            sym_diff = str(sym_diff),
            sym_frac = str(sym_frac),
            true_model = str(true_model),
            pred_model = str(sp_model)
            )

    print('result:',result)
    return result
