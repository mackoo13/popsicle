from typing import Set, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor
from wombat.ml_utils.weights_tuner import WeightsTuner
from wombat.ml_utils.data_set import DataSet
from wombat.ml_utils.ml_utils import regr_score
import numpy as np
import pandas as pd


def feature_ranking(data: DataSet) -> np.array:
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
           for i, (col, imp) in enumerate(zip(data.x.columns, regr.feature_importances_))]
    res = sorted(res, key=lambda q: q[2], reverse=True)
    return np.array(res)


def add_feats(data: DataSet, step: int, regr) -> Tuple[float, Set[str]]:
    """
    Applies a greedy algorithm to construct a subset of features giving a good score for the given regressor.
    In each iteration, it will select the 'best' feature of top 'step' features in the ranking.

    :param data: DataSet
    :param step: How many features from the top of the ranking will we considered in each iteration. Increasing the
                 step can improve the score, but takes considerably more time
    :param regr: Regressor
    :return:
    """
    feats_selected = set()
    feats_left = feature_ranking(data)[:, 1]
    best_score = float('-infinity')

    while len(feats_left) > 0:
        feats_to_check = feats_left[:step]
        feat_to_add = None
        new_best_score = best_score

        for feat in feats_to_check:
            new_feats = feats_selected.copy()
            new_feats.add(feat)

            new_data = DataSet(
                data.x[list(new_feats)],
                data.y
            )

            score = regr_score(new_data, regr)
            if score > best_score:
                new_best_score = score
                feat_to_add = feat

        if feat_to_add is not None:
            best_score = new_best_score
            feats_selected.add(feat_to_add)
            feats_left = [q for q in feats_left if q != feat_to_add]
        else:
            feats_left = feats_left[step:]

    return best_score, feats_selected


def remove_feats(data: DataSet, feats: Set[str], regr) -> Tuple[float, Set[str]]:
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
                data.x[list(new_feats)],
                data.y
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


class DimReducer:
    def __init__(self, how, n_neighbors_list={4, 8, 12}):
        """
        For description of 'greedy' strategy, see docs/algorithm/dimensionality_reduction.md.
        KNeighborsRegressor is assumed as the regressor, but can be easily changed to a different model.

        :param how: Which algorithm to use. Available: 'greedy', 'pca'
        :param n_neighbors_list: What n_neighbors values to test in the regressor
        """

        self.feats = None
        self.weights = None
        self.n_neighbors = None
        self.pca = None
        self.n_neighbors_list = list(n_neighbors_list)

        if how == 'pca': 
            self.fit = self.fit_pca
            self.transform = self.transform_pca
        elif how == 'greedy':
            self.fit = self.fit_greedy
            self.transform = self.transform_greedy
        else:
            raise ValueError('Unknown feature selection mode')

    def fit_pca(self, data: DataSet, pca_comp_list=None):
        if pca_comp_list is None:
            pca_comp_list = [8, 12, 16, 20]

        best_score = float('-infinity')
        best_pca = None
        best_n_neighbors = None

        print('Performing PCA')

        for pca_comp in pca_comp_list:

            pca = PCA(n_components=pca_comp)
            x = pca.fit_transform(data.x)
            x = pd.DataFrame(x)
            x.index = data.x.index
            new_data = DataSet(x, data.y)

            for n_neighbors in self.n_neighbors_list:
                regr = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')
                regr.fit(x, data.y)

                score = regr_score(new_data, regr)
                if score > best_score:
                    best_score = score
                    best_pca = pca
                    best_n_neighbors = n_neighbors

        print()
        print('\tBest score in training set:', round(best_score, 2))
        print('\tBest value of n_components:', best_pca.n_components)
        print('\tBest value of n_neighbors:', best_n_neighbors)
        print()

        self.pca = best_pca
        self.n_neighbors = best_n_neighbors

    def fit_greedy(self, data: DataSet, n_iter=10, step=5, require_tot_ins=True):
        best_score = float('-infinity')
        best_feats = None
        best_n_neighbors = None

        print('Performing step feature selection (step=%d, n_iter=%d)' % (step, n_iter))

        for n_neighbors in self.n_neighbors_list:
            regr = KNeighborsRegressor(n_neighbors=n_neighbors, weights='distance')

            for i in range(n_iter):
                print('\tIteration ' + str(i + 1) + '/' + str(n_iter) + ' for ' + str(n_neighbors) + ' neighbours')
                _, feats = add_feats(data, step, regr)
                score, _ = remove_feats(data, feats, regr)

                if score > best_score:
                    best_score = score
                    best_feats = feats
                    best_n_neighbors = n_neighbors

        feats_list = sorted(best_feats)
        if require_tot_ins and 'PAPI_TOT_INS' not in feats_list:
            feats_list.insert(0, 'PAPI_TOT_INS')

        print()
        print('\tBest score in training set:', round(best_score, 2))
        print('\tBest value of n_neighbors:', best_n_neighbors)
        print('\tSelected %d features:' % len(feats_list))
        print('\n'.join(['\t\t' + f for f in feats_list]))
        print()

        selected_data = DataSet(data.x[feats_list], data.y)
        regr = KNeighborsRegressor(n_neighbors=best_n_neighbors, weights='distance')
        wt = WeightsTuner(selected_data, regr)
        wt.fit()

        self.feats = feats_list
        self.n_neighbors = best_n_neighbors
        self.weights = wt.best_weights

    def transform_pca(self, x):
        return self.pca.transform(x)

    def transform_greedy(self, x):
        return np.multiply(x[self.feats], self.weights)
