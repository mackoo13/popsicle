from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor
from ml_utils.coeffs_learner import CoeffsLearner
from ml_utils.df_utils import DataSet
from ml_utils.ml_utils import calc_score
from ml_utils.nca import NCA
import numpy as np


def dim_sign(data: DataSet):
    """
    todo
    :param data:
    :return:
    """
    regr = RandomForestRegressor()
    regr.fit(data.x, data.y)
    res = [(i, col, imp)
           for i, (col, imp) in enumerate(zip(data.x_labels, regr.feature_importances_))]
    res = sorted(res, key=lambda q: q[2], reverse=True)
    return np.array(res)


def make_step_search(data: DataSet, step: int, clf):
    """
    todo
    :param data:
    :param step:
    :param clf:
    :return:
    """
    feats = set()
    left = dim_sign(data)[:, 0].astype(int)
    best = float('-infinity')

    while len(left) > 0:
        to_check = left[:step]
        to_add = None
        new_best = best

        for i in to_check:
            new_feats = feats.copy()
            new_feats.add(i)

            new_data = DataSet(
                data.x[:, list(new_feats)],
                data.y,
                data.df,
                data.x_labels[list(new_feats)]
            )

            score = calc_score(new_data, clf)
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


def remove_feats(data: DataSet, feats, clf):
    best = calc_score(data, clf)

    while True:
        to_remove = None

        if len(feats) == 1:
            break

        for f in feats:
            new_feats = feats.copy()
            new_feats.remove(f)

            new_data = DataSet(
                data.x[:, list(new_feats)],
                data.y,
                data.df,
                data.x_labels[list(new_feats)]
            )

            score = calc_score(new_data, clf)
            if score >= best:
                best = score
                to_remove = f

        if to_remove is not None:
            feats.remove(to_remove)
        else:
            break

    return best, feats


def feature_importance(data: DataSet, n_iter=100):
    res = {}
    for c in data.df.columns:
        res[c] = 0

    for i in range(n_iter):
        fs = DimReducer('step')
        fs.fit(data)
        feats = [data.df.columns[q] for q in fs.feats]
        for f in feats:
            res[f] += 1

    resl = [(k, v) for k, v in res.items()]
    resl = sorted(resl, key=lambda q: q[1], reverse=True)
    for k, v in resl:
        print(k, '\t', v)


class DimReducer:
    def __init__(self, how, n_neighbors_list={6}):
        self.feats = None
        self.coeffs = None
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
            raise ValueError('Unknown feature selection mode')

    def fit_pca(self, data: DataSet, pca_comp=14):
        pca = PCA(n_components=pca_comp)
        pca.fit(data.x)
        self.pca = pca

    def fit_nca(self, data: DataSet, nca_dim=6, nca_optimizer='gd'):
        nca = NCA(dim=nca_dim, optimizer=nca_optimizer)
        nca.fit(data.x, data.y)
        self.nca = nca

    def fit_step(self, data: DataSet, n_iter=10, step=5, require_tot_ins=True):
        best = float('-infinity')
        best_feats = None
        best_n_neighbors = None

        print('Performing step feature selection (step=%d, n_iter=%d)' % (step, n_iter))

        for n_neighbors in self.n_neighbors_list:
            clf = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')

            for i in range(n_iter):
                print('\tIteration ' + str(i + 1) + '/' + str(n_iter) + ' for ' + str(n_neighbors) + ' neighbours')
                _, feats = make_step_search(data, step, clf)
                score, _ = remove_feats(data, feats, clf)

                if score > best:
                    best = score
                    best_feats = feats
                    best_n_neighbors = n_neighbors

        feats_list = sorted(best_feats)
        if require_tot_ins and 'PAPI_TOT_INS' not in feats_list:
            feats_list.insert(0, list(data.df.columns).index('PAPI_TOT_INS'))

        print('Best score in training set:', round(best, 2))
        print('Best value of n_neighbors:', best_n_neighbors)
        print('Selected %d features:' % len(feats_list))
        print('\n'.join(['\t' + data.df.columns[f] for f in feats_list]))

        selected_data = DataSet(data.x[:, feats_list], data.y, data.df, data.x_labels)
        clf = KNeighborsRegressor(n_neighbors=best_n_neighbors, weights='distance')
        coeffs_learner = CoeffsLearner(selected_data, clf)
        coeffs_learner.fit()

        self.feats = feats_list
        self.n_neighbors = best_n_neighbors
        self.coeffs = coeffs_learner.best_coeffs

    def set_pca(self, pca):
        self.pca = pca

    def set_nca(self, nca):
        self.nca = nca

    def set_step(self, feats, coeffs):
        self.feats = feats
        self.coeffs = coeffs

    def transform_pca(self, x):
        return self.pca.transform(x)

    def transform_nca(self, x):
        return self.nca.transform(x)

    def transform_step(self, x):
        return np.multiply(x[:, self.feats], self.coeffs)
