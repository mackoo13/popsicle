from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score, GroupKFold
# noinspection PyUnresolvedReferences
from nca import NCA     # add "notebooks." if not used with Jupyter
import numpy as np


def adjust_r2(r2, n, k):
    """
    https://en.wikipedia.org/wiki/Coefficient_of_determination#Adjusted_R2
    :param r2: R2 score (unadjusted yet)
    :param n: Number of samples
    :param k: Number of features
    :return: Adjusted R2 score
    """
    nom = (1-r2) * (n-1)
    denom = n-k-1

    if denom <= 0:
        raise ValueError('At least ' + str(k+2) + ' samples needed to calculate adjusted R2 score')

    return 1 - (nom/denom)


def dim_sign(x, y, df):
    """
    todo
    :param x:
    :param y:
    :param df:
    :return:
    """
    regr = RandomForestRegressor()
    regr.fit(x, y)
    res = [(i, col, imp) for i, (col, imp) in enumerate(zip(df.columns, regr.feature_importances_))]
    res = sorted(res, key=lambda q: q[2], reverse=True)
    return np.array(res)


def calc_score(x, y, df, n_neighbors):
    """
    todo
    :param x:
    :param y:
    :param df:
    :param n_neighbors:
    :return:
    """
    clf = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')
    clf.fit(x, y)

    groups = list(df.index.get_level_values(0))
    cv = GroupKFold(n_splits=3).split(x, y, groups)
    score = cross_val_score(clf, x, y, cv=cv).mean()
    return adjust_r2(score, x.shape[0], x.shape[1])


def make_step_search(x, y, df, step, n_neighbors):
    """
    todo
    :param x:
    :param y:
    :param df:
    :param step:
    :param n_neighbors:
    :return:
    """
    feats = set()
    left = dim_sign(x, y, df)[:, 0].astype(int)
    best = float('-infinity')

    while len(left) > 0:
        to_check = left[:step]
        to_add = None
        new_best = best

        for i in to_check:
            new_feats = feats.copy()
            new_feats.add(i)
            x3 = x[:, list(new_feats)]

            score = calc_score(x3, y, df, n_neighbors)
            if score > best:
                new_best = score
                to_add = i

        if to_add is not None:
            best = new_best
            feats.add(to_add)
            left = [q for q in left if q != to_add]
        else:
            left = left[step:]

    return best, feats


def remove_feats(x, y, df, feats, n_neighbors):
    best = calc_score(x, y, df, n_neighbors)

    while True:
        to_remove = None

        if len(feats) == 1:
            break

        for f in feats:
            new_feats = feats.copy()
            new_feats.remove(f)
            x3 = x[:, list(new_feats)]
            score = calc_score(x3, y, df, n_neighbors)
            if score >= best:
                best = score
                to_remove = f

        if to_remove is not None:
            feats.remove(to_remove)
        else:
            break

    return best, feats


def feature_importance(x, y, df, n_iter=100):
    res = {}
    for c in df.columns:
        res[c] = 0

    for i in range(n_iter):
        fs = FeatureSelector('step')
        fs.fit(x, y, df)
        feats = [df.columns[q] for q in fs.feats]
        for f in feats:
            res[f] += 1

    resl = [(k, v) for k, v in res.items()]
    resl = sorted(resl, key=lambda q: q[1], reverse=True)
    for k, v in resl:
        print(k, '\t', v)


class FeatureSelector:
    def __init__(self, how, n_neighbors_list={6}):
        self.feats = None
        self.n_neighbors = None
        self.pca = None
        self.nca = None
        self.n_neighbors_list = list(n_neighbors_list)

        if how == 'pca': 
            self.fit = self.fit_pca
            self.transform = self.transform_pca
        elif how == 'nca':
            self.fit = self.fit_nca
            self.transform = self.transform_nca
        elif how == 'step':
            self.fit = self.fit_step
            self.transform = self.transform_step
        else:
            raise Exception('Unknown feature selection mode')

    def fit_pca(self, x, _y, _df, pca_comp=14):
        pca = PCA(n_components=pca_comp)
        pca.fit(x)
        self.pca = pca

    def fit_nca(self, x, y, _df, nca_dim=6, nca_optimizer='gd'):
        nca = NCA(dim=nca_dim, optimizer=nca_optimizer)
        nca.fit(x, y)
        self.nca = nca

    def fit_step(self, x, y, df, n_iter=10, step=5, require_tot_ins=True):
        best = float('-infinity')
        best_feats = None
        best_n_neighbors = None

        print('Performing step feature selection (step=%d, n_iter=%d)' % (step, n_iter))

        for n_neighbors in self.n_neighbors_list:
            for i in range(n_iter):
                print('Iteration ' + str(i + 1) + '/' + str(n_iter) + ' for ' + str(n_neighbors) + ' neighbours')
                _, feats = make_step_search(x, y, df, step, n_neighbors)
                score, _ = remove_feats(x, y, df, feats, n_neighbors)

                if score > best:
                    best = score
                    best_feats = feats
                    best_n_neighbors = n_neighbors

        feats_list = sorted(best_feats)
        if require_tot_ins and 'PAPI_TOT_INS' not in feats_list:
            feats_list.insert(0, list(df.columns).index('PAPI_TOT_INS'))

        print('Best score in training set:', round(best, 2))
        print('Best value of n_neighbors:', best_n_neighbors)
        print('Selected %d features:' % len(feats_list))
        print('\n'.join(['\t' + df.columns[f] for f in feats_list]))

        self.feats = feats_list
        self.n_neighbors = best_n_neighbors

    def transform_pca(self, x):
        return self.pca.transform(x)

    def transform_nca(self, x):
        return self.nca.transform(x)

    def transform_step(self, x):
        return x[:, self.feats]
