from __future__ import print_function
import argparse
import os
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.externals import joblib


out_dir = os.environ["LORE_PAPI_OUT_DIR"]
model_dir = os.environ["LORE_MODELS_DIR"]
n_components = 2
n_neighbors = 10


def aggregate(df):
    return df.groupby(['alg', 'run'])[df.columns[2:55]].min()


def load_data(files, scaler=None):
    print('Loading files: ', files)
    paths = [out_dir + p for p in files]

    dfs = [pd.read_csv(path, error_bad_lines=False) for path in paths]
    df = pd.concat(dfs)
    df['run'] = df['run'].astype(str)
    df = aggregate(df)

    df = df.loc[df['time'] > 0]

    cols = sorted(list(df.columns.values))
    df = df[cols]
    df = df.astype('float64')

    x = df.drop(['time'], axis=1).values
    y = df['time'].values

    if scaler is None:
        scaler = StandardScaler()
        x = scaler.fit_transform(x)
    else:
        x = scaler.transform(x)

    print('Samples:', df.shape[0])
    print('Features:', df.shape[1]-1)

    return x, y, df, scaler


def score(x, y, df, clf):
    groups = list(df.index.get_level_values(0))
    cv = GroupKFold(n_splits=3).split(x, y, groups)

    scores = cross_val_score(clf, x, y, cv=list(cv))
    return scores.mean()


def do_pca(x):
    print('Performing PCA dimensionality reduction (n_components=' + str(n_components) + ')...')
    pca = PCA(n_components=n_components)
    x = pca.fit_transform(x)
    print('PCA explained variance: %.2f' % pca.explained_variance_ratio_.sum())

    return x, pca


def do_neigh_regr(x, y):
    print('Training KNeighborsRegressor (n_neighbors=' + str(n_neighbors) + ')...')
    neigh = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')
    neigh.fit(x, y)
    return neigh


def save_models(scaler, pca, clf):
    print('Finished training. Saving the models to ' + model_dir + '...')
    joblib.dump(scaler, model_dir + 'scaler.pkl')
    joblib.dump(pca, model_dir + 'pca.pkl')
    joblib.dump(clf, model_dir + 'clf.pkl')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', action='append', required=True, help='<Required> input files in CSV format. '
                                                                              'You can provide multiple files '
                                                                              '(-i file1.csv -i file2.csv...).')
    args = parser.parse_args()
    files = args.input

    x, y, df, scaler = load_data(files)
    x, pca = do_pca(x)
    clf = do_neigh_regr(x, y)

    save_models(scaler, pca, clf)

    print('R2 score: %.2f' % score(x, y, df, clf))


if __name__ == "__main__":
    main()
