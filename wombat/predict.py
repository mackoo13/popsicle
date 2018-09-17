from __future__ import print_function
import argparse
import os
from sklearn.externals import joblib
from wombat.ml_utils.file_loader import FileLoader
from wombat.utils import check_config

check_config(['PAPI_OUT_DIR', 'LORE_MODELS_DIR'])

out_dir = os.environ['PAPI_OUT_DIR']
model_dir = os.environ['LORE_MODELS_DIR']


def load_models():
    scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
    dim_reducer = joblib.load(os.path.join(model_dir, 'dim_reducer.pkl'))
    regr = joblib.load(os.path.join(model_dir, 'regr.pkl'))
    return scaler, dim_reducer, regr


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
        raise ValueError('Unsupported mode: ' + mode)

    scaler, dim_reducer, regr = load_models()
    fl = FileLoader(files, mode=mode, purpose='predict', scaler=scaler)

    x = dim_reducer.transform(fl.data.full_set.x)
    y = regr.predict(x)

    print(regr.score(x, fl.data.full_set.y))

    # for yp, yr in zip(y[:9], fl.data.full_set.y[:9]):
    #     print(round(yp, 2), '\t', round(yr, 2))


if __name__ == "__main__":
    main()
