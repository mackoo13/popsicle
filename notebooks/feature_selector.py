from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score, GroupKFold
# noinspection PyUnresolvedReferences
from nca import NCA     # add "notebooks." if not used with Jupyter
import numpy as np


def dim_sign(x, y, df):
    regr = RandomForestRegressor()
    regr.fit(x, y)
    res = [(i, col, imp) for i, (col, imp) in enumerate(zip(df.columns, regr.feature_importances_))]
    res = sorted(res, key=lambda q: q[2], reverse=True)
    return np.array(res)


def calc_score(x, y, df):
    clf = KNeighborsRegressor(n_neighbors=6, weights='distance')
    clf.fit(x, y)

    groups = list(df.index.get_level_values(0))
    cv = GroupKFold(n_splits=3).split(x, y, groups)
    score = cross_val_score(clf, x, y, cv=cv).mean()
    return score


def make_step_search(x, y, df, step):
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

            score = calc_score(x3, y, df)
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


def remove_feats(x, y, df, feats):
    best = calc_score(x, y, df)

    while True:
        to_remove = None

        for f in feats:
            new_feats = feats.copy()
            new_feats.remove(f)
            x3 = x[:, list(new_feats)]
            score = calc_score(x3, y, df)
            if score > best:
                best = score
                to_remove = f

        if to_remove is not None:
            feats.remove(to_remove)
        else:
            break

    return best, feats


class FeatureSelector:
    def __init__(self, how):
        self.feats = None
        self.pca = None
        self.nca = None

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
        print('Explained variance:', pca.explained_variance_ratio_.sum())
        self.pca = pca

    def fit_nca(self, x, y, _df, nca_dim=6, nca_optimizer='gd'):
        nca = NCA(dim=nca_dim, optimizer=nca_optimizer)
        nca.fit(x, y)
        self.nca = nca

    def fit_step(self, x, y, df):
        n_iter = 5
        step = 5
        best = float('-infinity')
        best_feats = None

        print('Performing step feature selection (step=%d, n_iter=%d)' % (step, n_iter))

        for i in range(n_iter):
            score, feats = make_step_search(x, y, df, step)
            if score > best:
                best = score
                best_feats = feats
            print('Iteration', i + 1, '/', n_iter)

        best, _ = remove_feats(x, y, df, best_feats)

        feats_list = sorted(best_feats)

        print('Best score in training set:', round(best, 2))
        print('Selected %d features:' % len(feats_list))
        print('\n'.join(['\t' + df.columns[f] for f in feats_list]))

        self.feats = feats_list

    def transform_pca(self, x):
        return self.pca.transform(x)

    def transform_nca(self, x):
        return self.nca.transform(x)

    def transform_step(self, x):
        return x[:, self.feats]
