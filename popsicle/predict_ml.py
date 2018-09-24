from __future__ import print_function
import argparse
import os
from sklearn.externals import joblib
from popsicle.ml_utils.file_loader import FileLoader
from popsicle.utils import check_config

check_config(['OUT_DIR', 'MODELS_DIR'])

out_dir = os.environ['OUT_DIR']
model_dir = os.environ['MODELS_DIR']


def load_models():
    scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
    dim_reducer = joblib.load(os.path.join(model_dir, 'dim_reducer.pkl'))
    regr = joblib.load(os.path.join(model_dir, 'regr.pkl'))
    return scaler, dim_reducer, regr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', action='append', required=True,
                        help='<Required> input files in CSV format (names without extensions). You can provide multiple'
                             ' files (-i file1 -i file2...).')
    args = parser.parse_args()
    files = args.input

    scaler, dim_reducer, regr = load_models()
    fl = FileLoader(files, mode='p', scaler=scaler)

    x = dim_reducer.transform(fl.data.full_set.x)
    y = regr.predict(x)

    # print(regr.score(x, fl.data.full_set.y))
    print('Predicted time/speedup: ' + str(y))


if __name__ == "__main__":
    main()
