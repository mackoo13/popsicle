from sklearn import clone
from sklearn.model_selection import GroupKFold, cross_val_score
from popsicle.ml_utils.df_utils import df_get_index_col, DataSet


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


def regr_score(data: DataSet, regr) -> float:
    """
    Calculates adjusted R2 score of a regressor for given data.
    """
    regr = clone(regr)
    regr.fit(data.x, data.y)

    groups = list(df_get_index_col(data.x, 'alg'))
    cv = GroupKFold(n_splits=3).split(data.x, data.y, groups)
    score = cross_val_score(regr, data.x, data.y, cv=cv).mean()
    return adjust_r2(score, data.x.shape[0], data.x.shape[1])
