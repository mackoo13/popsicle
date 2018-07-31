from __future__ import print_function
import argparse
import pandas as pd
from sklearn.externals import joblib


out_dir = '~/ftb/papi_output/'
model_dir = '~/ftb/wombat/lore/models/'
n_components = 2
n_neighbors = 10


def load_models(path='models/'):
    scaler = joblib.load(path + 'scaler.pkl')
    pca = joblib.load(path + 'pca.pkl')
    clf = joblib.load(path + 'clf.pkl')
    return scaler, pca, clf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='<Required> input file in CSV format.')
    args = parser.parse_args()
    file = args.input

    scaler, pca, clf = load_models()

    df = pd.read_csv(file)
    cols = sorted(list(df.columns.values))
    df = df[cols]

    x = df.drop('time', axis=1).values
    x = scaler.transform(x)
    x = pca.transform(x)
    y = clf.predict(x)

    print('Predicted time:', y[0])


if __name__ == "__main__":
    main()
