from __future__ import print_function
import argparse
import os
from sklearn.externals import joblib

from ml_utils.file_loader import FileLoader
from utils import check_config

check_config(['PAPI_OUT_DIR', 'LORE_MODELS_DIR'])

out_dir = os.environ['PAPI_OUT_DIR']
model_dir = os.environ['LORE_MODELS_DIR']


def load_models():
    scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
    dim_reducer = joblib.load(os.path.join(model_dir, 'dim_reducer.pkl'))
    clf = joblib.load(os.path.join(model_dir, 'clf.pkl'))
    return scaler, dim_reducer, clf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', type=str, help='todo')
    parser.add_argument('-i', '--input', action='append', required=True,
                        help='<Required> input files in CSV format (names without extensions). You can provide multiple'
                             ' files (-i file1 -i file2...).')
    args = parser.parse_args()
    mode = args.mode
    files = args.input

    if mode not in ('time', 't', 'speedup', 's', 'unroll', 'u'):
        raise ValueError('Unsupported mode')

    scaler, dim_reducer, clf = load_models()
    fl = FileLoader(files, mode=mode, purpose='predict', scaler=scaler)

    x = dim_reducer.transform(fl.x)
    y = clf.predict(x)

    print('Prediction:', y)


if __name__ == "__main__":
    main()
