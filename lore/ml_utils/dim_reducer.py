from typing import Set, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor
from ml_utils.coeffs_learner import CoeffsLearner
from ml_utils.data_set import DataSet
from ml_utils.ml_utils import regr_score
from ml_utils.nca import NCA
import numpy as np


def dim_sign(data: DataSet) -> np.array:
    """
    Orders the features by their importance according to RandomForestRegressor.
    RandomForestRegressor is not deterministic, so generating the list multiple times is recommended for better results.
    See http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
    :param data: DataSet to train
    :return: A list of tuples ordered by the importance (descendingly):
        (feature index, feature name, importance)
    """
    regr = RandomForestRegressor()
    regr.fit(data.x, data.y)
    res = [(i, col, imp)
           for i, (col, imp) in enumerate(zip(data.x_labels, regr.feature_importances_))]
    res = sorted(res, key=lambda q: q[2], reverse=True)
    return np.array(res)


def make_step_search(data: DataSet, step: int, regr):
    """
    todo
    :param data:
    :param step:
    :param regr:
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

            score = regr_score(new_data, regr)
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


def remove_feats(data: DataSet, feats: Set[int], regr) -> Tuple[float, Set[int]]:
    """
    This is the second phase of selecting the optimal subset of features. It takes the existing subset and tries to
    remove redundant features as long as the score does not decrease.
    :param data: Dataset to learn
    :param feats: Existing subset of features (as a set of indices)
    :param regr: Regressor to evaluate solutions
    :return: The best achieved score and the subset of features
    """
    best = regr_score(data, regr)

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

            score = regr_score(new_data, regr)
            if score >= best:
                best = score
                to_remove = f

        if to_remove is not None:
            feats.remove(to_remove)
        else:
            break

    return best, feats


def feature_importance(data: DataSet, n_iter=100):
    """
    Creates a ranking of features by how often they are selected as useful.
    Basically, feature selection is performed n_iter times and the results are aggregated.
    Warning: the result might be misleading. Use with care.
    :param data: DataSet to learn
    :param n_iter: Number of times to perform feature selection
    :return:
    """
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
        """
        For description of 'step' strategy, see docs/algorithm/dimensionality_reduction.md.
        KNeighborsRegressor is assumed as the regressor, but can be easily changed to a different model.

        :param how: Which algorithm to use. Available: 'step', 'pca', 'nca'
        :param n_neighbors_list: What n_neighbors values to test in the regressor
        """

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
            regr = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')

            for i in range(n_iter):
                print('\tIteration ' + str(i + 1) + '/' + str(n_iter) + ' for ' + str(n_neighbors) + ' neighbours')
                _, feats = make_step_search(data, step, regr)
                score, _ = remove_feats(data, feats, regr)

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
        regr = KNeighborsRegressor(n_neighbors=best_n_neighbors, weights='distance')
        coeffs_learner = CoeffsLearner(selected_data, regr)
        coeffs_learner.fit()

        self.feats = feats_list
        self.n_neighbors = best_n_neighbors
        self.coeffs = coeffs_learner.best_coeffs

    def transform_pca(self, x):
        return self.pca.transform(x)

    def transform_nca(self, x):
        return self.nca.transform(x)

    def transform_step(self, x):
        return np.multiply(x[:, self.feats], self.coeffs)
