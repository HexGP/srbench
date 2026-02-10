import sys
import itertools
import pandas as pd
from sklearn.base import clone
from sklearn.experimental import enable_halving_search_cv # noqa
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
try:
    from sklearn.metrics import mean_absolute_percentage_error
except ImportError:
    mean_absolute_percentage_error = None  # added in sklearn 0.24
from sklearn.model_selection import train_test_split
import warnings
import time
from tempfile import mkdtemp
from shutil import rmtree
from joblib import Memory
from read_file import read_file
import pdb
import numpy as np
import json
import os
import inspect
from utils import jsonify
from symbolic_utils import get_sym_model

from metrics.evaluation import simplicity

import signal
class TimeOutException(Exception):
    pass

def alarm_handler(signum, frame):
    print(f"raising TimeOutException")
    raise TimeOutException

def set_env_vars(n_jobs):
    os.environ['OMP_NUM_THREADS'] = n_jobs 
    os.environ['OPENBLAS_NUM_THREADS'] = n_jobs 
    os.environ['MKL_NUM_THREADS'] = n_jobs

def evaluate_model(
    dataset, 
    results_path,
    random_state,
    est_name,
    est,
    model,
    test=False,
    sym_data=False,
    target_noise=0.0, 
    feature_noise=0.0, 
    ##########
    # valid options for eval_kwargs
    ##########
    test_params={},
    max_train_samples=0,
    scale_x=True,
    scale_y=True,
    pre_train=None,
    use_dataframe=True
):

    print(40*'=','Evaluating '+est_name+' on ',dataset,40*'=',sep='\n')

    np.random.seed(random_state)
    if hasattr(est, 'random_state'):
        est.random_state = random_state

    ##################################################
    # setup data
    ##################################################

    ##################################################
    # setup data
    ##################################################
    features, labels, feature_names =  read_file(
        dataset, 
        use_dataframe=use_dataframe
    )
    print('feature_names:',feature_names)
    if sym_data:
        true_model = get_sym_model(dataset)
    # generate train/test split
    X_train, X_test, y_train, y_test = train_test_split(features, labels,
                                                    train_size=0.80,
                                                    test_size=0.20,
                                                    random_state=random_state)

    # time limits
    MAXTIME = 3600
    if len(y_train) > 1000:
        MAXTIME = 36000

    print('max time:',MAXTIME)

    # if dataset is large, subsample the training set 
    if max_train_samples > 0 and len(y_train) > max_train_samples:
        print('subsampling training data from',len(X_train),
              'to',max_train_samples)
        sample_idx = np.random.choice(np.arange(len(X_train)),
                                      size=max_train_samples)
        y_train = y_train[sample_idx]
        if isinstance(X_train, pd.DataFrame):
            X_train = X_train.loc[sample_idx]
        else:
            X_train = X_train[sample_idx]

    # ENB and Agric: use MinMaxScaler + 1e-6 (match codes/ENB/mtr_ginn_sym.py, codes/Agriculture/mtr_ginn_agric_sym.py)
    # Agric only: log-transform targets so models predict in log space
    is_agric = 'agric' in dataset
    is_enb = 'enb' in dataset
    use_y_inverse = scale_y  # whether to inverse-transform predictions when scoring
    y_test_scaled = None     # set for agric/enb so scoring uses correct target

    if is_agric or is_enb:
        # X: MinMaxScaler then + 1e-6 (same as reference scripts)
        X_train_arr = np.asarray(X_train) if not isinstance(X_train, np.ndarray) else X_train
        X_test_arr = np.asarray(X_test) if not isinstance(X_test, np.ndarray) else X_test
        sc_X = MinMaxScaler()
        X_train_scaled = sc_X.fit_transform(X_train_arr) + 1e-6
        X_test_scaled = sc_X.transform(X_test_arr) + 1e-6
        if use_dataframe:
            X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_names)
            X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_names)
        if is_agric:
            y_train_scaled = np.log(np.asarray(y_train, dtype=np.float64))
            y_test_scaled = np.log(np.asarray(y_test, dtype=np.float64))
            use_y_inverse = False  # predictions are in log space; score vs log(y)
        else:
            y_train_scaled = np.asarray(y_train) if not isinstance(y_train, np.ndarray) else y_train
            y_test_scaled = np.asarray(y_test) if not isinstance(y_test, np.ndarray) else y_test
            use_y_inverse = False
        print('scaling X with MinMaxScaler+1e-6' + ('; y in log space (agric)' if is_agric else ''))
    else:
        # scale and normalize the data (default)
        if scale_x:
            print('scaling X')
            sc_X = StandardScaler()
            X_train_scaled = sc_X.fit_transform(X_train)
            X_test_scaled = sc_X.transform(X_test)
            if use_dataframe:
                X_train_scaled = pd.DataFrame(X_train_scaled,
                                              columns=feature_names)
                X_test_scaled = pd.DataFrame(X_test_scaled,
                                              columns=feature_names)
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test

        if scale_y:
            print('scaling y')
            sc_y = StandardScaler()
            y_train_scaled = sc_y.fit_transform(y_train.reshape(-1,1)).flatten()
        else:
            y_train_scaled = y_train
        if not scale_y:
            y_test_scaled = y_test
        else:
            y_test_scaled = sc_y.transform(y_test.reshape(-1,1)).flatten()


    ################################################## 
    # noise
    ################################################## 
    if target_noise > 0:
        print('adding',target_noise,'noise to target')
        y_train_scaled += np.random.normal(0, 
                    target_noise*np.sqrt(np.mean(np.square(y_train_scaled))),
                    size=len(y_train_scaled))
    # add noise to the features
    if feature_noise > 0:
        print('adding',target_noise,'noise to features')
        X_train_scaled = np.array([x 
            + np.random.normal(0, feature_noise*np.sqrt(np.mean(np.square(x))),
                               size=len(x))
                                   for x in X_train_scaled.T]).T

    ################################################## 
    # run any method-specific pre_train routines
    ################################################## 
    if pre_train:
        pre_train(est, X_train_scaled, y_train_scaled)

    # define a test mode using estimator test_params, if they exist
    if test and len(test_params) != 0:
        est.set_params(**test_params)

    ################################################## 
    # Fit models
    ################################################## 
    if not use_dataframe: 
        assert isinstance(X_train_scaled, np.ndarray)
        assert isinstance(X_test_scaled, np.ndarray)
    print('X_train:',type(X_train_scaled),X_train_scaled.shape)
    print('y_train:',y_train_scaled.shape)
    print('training',est)
    t0t = time.time()
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(MAXTIME) # maximum time, defined above
    try:
        est.fit(X_train_scaled, y_train_scaled)
    except TimeOutException:
        print('WARNING: fitting timed out')

    time_time = time.time() - t0t
    print('Training time measure:', time_time)
    
    ##################################################
    # store results
    ##################################################
    dataset_name = dataset.split('/')[-1].split('.')[0]
    results = {
        'dataset':dataset_name,
        'algorithm':est_name,
        'params':jsonify(est.get_params()),
        'random_state':random_state,
        'time_time': time_time, 
    }
    if sym_data:
        results['true_model'] = true_model

    # get the final symbolic model as a string
    print('fitted est:',est)

    if 'X' in inspect.signature(model).parameters.keys():
        if not isinstance(X_train_scaled, pd.DataFrame):
            X_df = pd.DataFrame(X_train_scaled, 
                                          columns=feature_names)
        else:
            X_df = X_train_scaled
        results['symbolic_model'] = model(est, X_df)
    else:
        results['symbolic_model'] = model(est)
    print('symbolic model:',results['symbolic_model'])
    ##################################################
    # scores
    ##################################################

    # For agric/enb we score in scaled space (log(y) for agric); for default scale_y we score in original space
    train_target = y_train if use_y_inverse else y_train_scaled
    test_target = y_test if use_y_inverse else y_test_scaled
    for fold, target, X in [
            ['train', train_target, X_train_scaled],
            ['test', test_target, X_test_scaled]
    ]:
        y_pred = np.asarray(est.predict(X)).reshape(-1, 1)
        if use_y_inverse:
            y_pred = sc_y.inverse_transform(y_pred)

        scorers = [
            ('mse', mean_squared_error),
            ('mae', mean_absolute_error),
            ('r2', r2_score),
        ]
        if mean_absolute_percentage_error is not None:
            scorers.append(('mape', mean_absolute_percentage_error))
        for score, scorer in scorers:
            try:
                val = scorer(target, y_pred)
                # MAPE can be inf/nan if target has zeros; store None so JSON is valid
                if score == 'mape' and (val is None or not np.isfinite(val)):
                    results[score + '_' + fold] = None
                else:
                    results[score + '_' + fold] = val
            except Exception:
                results[score + '_' + fold] = None

    if mean_absolute_percentage_error is None:
        results['mape_train'] = None
        results['mape_test'] = None

    # RMSE = sqrt(MSE), saved so you can read it directly from JSON
    results['rmse_train'] = float(np.sqrt(results['mse_train'])) if results.get('mse_train') is not None else None
    results['rmse_test'] = float(np.sqrt(results['mse_test'])) if results.get('mse_test') is not None else None

    # simplicity
    results['simplicity'] = simplicity(results['symbolic_model'], feature_names)

    ##################################################
    # write to file
    ##################################################
    print('results:')
    print(json.dumps(results,indent=4))
    print('---')

    if not os.path.exists(results_path):
        os.makedirs(results_path)

    # Prefix filename with estimator type so files in .results can be grouped easily
    if 'DSR' in est_name:
        prefix = 'DSR_'
    elif 'BSR' in est_name:
        prefix = 'BSR_'
    elif 'AIF' in est_name or 'Feyn' in est_name:
        prefix = 'AIfey_'
    else:
        prefix = ''

    base_name = prefix + dataset_name + '_' + est_name + '_' + str(random_state)
    if target_noise > 0:
        base_name += '_target-noise' + str(target_noise)
    if feature_noise > 0:
        base_name += '_feature-noise' + str(feature_noise)

    save_file = os.path.join(results_path, base_name)

    print('save_file:',save_file)

    with open(save_file + '.json', 'w') as out:
        json.dump(jsonify(results), out, indent=4)

    return save_file + '.json'

################################################################################
# main entry point
################################################################################
import argparse
import importlib

if __name__ == '__main__':

    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="Evaluate a method on a dataset.", add_help=False)
    parser.add_argument('INPUT_FILE', type=str,
                        help='Data file to analyze; ensure that the '
                        'target/label column is labeled as "class".')    
    parser.add_argument('-h', '--help', action='help',
                        help='Show this help message and exit.')
    parser.add_argument('-ml', action='store', dest='ALG',default=None,type=str, 
            help='Name of estimator (with matching file in methods/)')
    parser.add_argument('-results_path', action='store', dest='RDIR',
                        default='results_test', type=str, 
                        help='Name of save file')
    parser.add_argument('-seed', action='store', dest='RANDOM_STATE',
                        default=42, type=int, help='Seed / trial')
    parser.add_argument('-test',action='store_true', dest='TEST', 
                       help='Used for testing a minimal version')
    parser.add_argument('-n_jobs',action='store',  type=str, default='4',
                        help='number of cores available')
    parser.add_argument('-max_samples',action='store',  type=int, default=0,
                        help='number of training samples')
    parser.add_argument('-target_noise',action='store',dest='Y_NOISE',
                        default=0.0, type=float, help='Gaussian noise to add'
                        'to the target')
    parser.add_argument('-feature_noise',action='store',dest='X_NOISE',
                        default=0.0, type=float, help='Gaussian noise to add'
                        'to the target')
    parser.add_argument('-sym_data',action='store_true',  
                       help='Use symbolic dataset settings')
    parser.add_argument('-skip_tuning',action='store_true', dest='SKIP_TUNE', 
                        default=False, help='Dont tune the estimator')

    args = parser.parse_args()
    set_env_vars(args.n_jobs)
    # import algorithm 
    # Tuned methods are imported directly, others use .regressor
    if args.ALG.startswith('tuned.'):
        import_path = 'methods.'+args.ALG
        print('import from', import_path)
        algorithm = importlib.__import__(import_path,
                                         globals(),
                                         locals(),
                                         ['*']
                                        )
    else:
        import_path = 'methods.'+args.ALG+'.regressor'
        print('import from', import_path)
        algorithm = importlib.__import__(import_path,
                                     globals(),
                                     locals(),
                                     ['*']
                                    )

    print('algorithm:',algorithm.est)

    # optional keyword arguments passed to evaluate
    eval_kwargs, test_params = {},{}
    if 'eval_kwargs' in dir(algorithm):
        eval_kwargs = algorithm.eval_kwargs

    if args.max_samples != 0:
        eval_kwargs['max_train_samples'] = args.max_samples

    evaluate_model(args.INPUT_FILE,
                   args.RDIR,
                   args.RANDOM_STATE,
                   args.ALG,
                   algorithm.est,  
                   algorithm.model, 
                   test = args.TEST, 
                   **eval_kwargs
                  )
