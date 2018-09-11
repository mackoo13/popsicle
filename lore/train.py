from __future__ import print_function
import argparse
import os
from sklearn.neighbors import KNeighborsRegressor
from sklearn.externals import joblib
from ml_utils.feature_selector import FeatureSelector
from ml_utils.file_loader import FileLoader
from ml_utils.ml_utils import adjust_r2
from utils import check_config

check_config(['PAPI_OUT_DIR', 'LORE_MODELS_DIR'])

out_dir = os.environ['PAPI_OUT_DIR']
model_dir = os.environ['LORE_MODELS_DIR']
n_components = 2
n_neighbors = 10


def save_models(scaler, pca, clf):
    print('Finished training. Saving the models to ' + model_dir + '...')
    joblib.dump(scaler, model_dir + 'scaler.pkl')
    joblib.dump(pca, model_dir + 'pca.pkl')
    joblib.dump(clf, model_dir + 'clf.pkl')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help='todo')
    parser.add_argument('-i', '--input', action='append', required=True,
                        help='<Required> input files in CSV format (names without extensions). You can provide multiple'
                             ' files (-i file1 -i file2...).')
    args = parser.parse_args()
    mode = args.mode
    files = args.input

    n_neighbors_list = [8]
    # fs_mode_list = ['step', 'pca', 'nca']
    fs_mode_list = ['step']
    fs_step = 5
    fs_n_iter = 1

    if mode not in ('time', 't', 'speedup', 's', 'unroll', 'u'):
        raise ValueError('Unsupported mode')

    fl = FileLoader(files, mode=mode)

    for fs_mode in fs_mode_list:
        fl.split()

        fs = FeatureSelector(fs_mode, n_neighbors_list=n_neighbors_list)
        fs.fit(fl.x_train, fl.y_train, fl.df_train, step=fs_step, n_iter=fs_n_iter)
        x = fs.transform(fl.x_train)
        x_test = fs.transform(fl.x_test)
        y, y_test = fl.y_train, fl.y_test

        clf = KNeighborsRegressor(n_neighbors=fs.n_neighbors, weights='distance')
        clf.fit(x, y)
        score = clf.score(x_test, y_test)
        adjusted = adjust_r2(score, x_test.shape[0], x_test.shape[1])

        print('r2:', round(score, 2), round(adjusted, 2))


if __name__ == "__main__":
    main()
