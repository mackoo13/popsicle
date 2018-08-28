from __future__ import print_function
import argparse
import os

import pandas as pd
from sklearn.externals import joblib


if 'PAPI_OUT_DIR' not in os.environ or 'LORE_MODELS_DIR' not in os.environ:
    print('Invalid config')
    exit(1)

out_dir = os.environ['PAPI_OUT_DIR']
model_dir = os.environ['LORE_MODELS_DIR']
n_components = 2
n_neighbors = 10


def load_models(path):
    scaler = joblib.load(path + 'scaler_opt.pkl')
    pca = joblib.load(path + 'pca_opt.pkl')
    clf = joblib.load(path + 'clf_opt.pkl')
    return scaler, pca, clf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='<Required> input file in CSV format.')
    args = parser.parse_args()
    file = args.input

    scaler, pca, clf = load_models(model_dir)

    df = pd.read_csv(file)
    cols = sorted(list(df.columns.values))
    df = df[cols]

    x = df.drop('time', axis=1).values
    x = scaler.transform(x)
    x = pca.transform(x)
    y = clf.predict(x)

    print('Predicted speedup:', y[0])


if __name__ == "__main__":
    main()
