from __future__ import print_function
import argparse
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.externals import joblib


out_dir = '/home/maciej/ftb/papi_output_opt/'
model_dir = '/home/maciej/ftb/wombat/models/'
n_components = 2
n_neighbors = 10


def aggregate(df):
    return df.groupby(['alg', 'run'])[df.columns[2:55]].min()


def load_df(paths, suffix):
    dfs = [pd.read_csv(path + suffix + '.csv', error_bad_lines=False) for path in paths]
    df = pd.concat(dfs)
    df['run'] = df['run'].astype(str)
    return df


def scale_tot_ins(df):
    for col in df.columns:
        if col[:4] == 'PAPI' and col != 'PAPI_TOT_INS':
            df[col] = df[col].astype(float).div(df['PAPI_TOT_INS'], axis=0)
    df['PAPI_TOT_INS'] = 1
    return df.dropna()


def load_data(files, scaler=None):
    print('Loading files: ', files)
    paths = [out_dir + p for p in files]

    df_o0 = load_df(paths, '_O0')
    df_o0 = aggregate(df_o0)

    df_o3 = load_df(paths, '_O3')
    df_o3 = df_o3[['alg', 'run', 'time_O3']]
    df_o3 = aggregate(df_o3)

    df = df_o0.merge(df_o3, left_index=True, right_index=True)
    df = df.loc[df['time_O3'] > 1]

    df = scale_tot_ins(df)
    df['speedup'] = df['time_O0'] / df['time_O3']

    cols = sorted(list(df.columns.values))
    df = df[cols]
    df = df.astype('float64')

    x = df.drop(['time_O0', 'time_O3', 'speedup'], axis=1).values
    y = df['speedup'].values

    if scaler is None:
        scaler = RobustScaler(quantile_range=(10, 90))
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
    safe_n_neighbors = min(n_neighbors, len(x))
    print('Training KNeighborsRegressor (n_neighbors=' + str(safe_n_neighbors) + ')...')
    neigh = KNeighborsRegressor(n_neighbors=safe_n_neighbors, weights='distance')
    neigh.fit(x, y)
    return neigh


def save_models(scaler, pca, clf):
    print('Finished training. Saving the models to ' + model_dir + '...')
    joblib.dump(scaler, model_dir + 'scaler_opt.pkl')
    joblib.dump(pca, model_dir + 'pca_opt.pkl')
    joblib.dump(clf, model_dir + 'clf_opt.pkl')


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

    try:
        print('R2 score: %.2f' % score(x, y, df, clf))
    except ValueError as e:
        print('Cannot calculate score (probable reason: not enough samples)')
        print(e)


if __name__ == "__main__":
    main()
