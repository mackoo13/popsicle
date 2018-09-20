from __future__ import print_function
import argparse
import os
from sklearn.neighbors import KNeighborsRegressor
from sklearn.externals import joblib
from wombat.ml_utils.dim_reducer import DimReducer
from wombat.ml_utils.file_loader import FileLoader
from wombat.ml_utils.ml_utils import adjust_r2
from wombat.utils import check_config

check_config(['PAPI_OUT_DIR', 'LORE_MODELS_DIR'])

out_dir = os.environ['PAPI_OUT_DIR']
model_dir = os.environ['LORE_MODELS_DIR']


def save_models(scaler, dim_reducer, regr):
    print('Finished training. Saving the models to ' + model_dir + '...')
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
    joblib.dump(dim_reducer, os.path.join(model_dir, 'dim_reducer.pkl'))
    joblib.dump(regr, os.path.join(model_dir, 'regr.pkl'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help='Use \'time\'/\'t\' for execution time prediction, '
                                               '\'speedup\'/\'s\' for predicting speedup after gcc optimisation or '
                                               '\'unroll\'/\'u\' for predicting speedup after clang loop unrolling.')
    parser.add_argument('-i', '--input', action='append', required=True,
                        help='<Required> input files in CSV format (names without extensions). You can provide multiple'
                             ' files (-i file1 -i file2...).')
    args = parser.parse_args()
    mode = args.mode
    files = args.input

    if mode not in ('time', 't', 'speedup', 's', 'unroll', 'u'):
        raise ValueError('Unsupported mode')

    n_neighbors_list = [4, 8, 12]
    # dr_mode_list = ['greedy', 'pca']
    dr_mode_list = ['greedy']
    dr_step = 5
    dr_n_iter = 3

    fl = FileLoader(files, mode=mode)

    for dr_mode in dr_mode_list:
        fl.data.split()

        dr = DimReducer(dr_mode, n_neighbors_list=n_neighbors_list)
        dr.fit(fl.data.train_set, step=dr_step, n_iter=dr_n_iter)
        x = dr.transform(fl.data.train_set.x)
        x_test = dr.transform(fl.data.test_set.x)
        y, y_test = fl.data.train_set.y, fl.data.test_set.y

        regr = KNeighborsRegressor(n_neighbors=dr.n_neighbors, weights='distance')
        regr.fit(x, y)
        score = regr.score(x_test, y_test)
        adjusted = adjust_r2(score, x_test.shape[0], x_test.shape[1])

        print('Score in test set:', round(adjusted, 2))
        save_models(fl.data.scaler, dr, regr)


if __name__ == "__main__":
    main()
