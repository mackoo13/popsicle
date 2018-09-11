from sklearn import clone
from sklearn.model_selection import GroupKFold, cross_val_score


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


def calc_score(x, y, df, clf):
    """
    todo
    :param x:
    :param y:
    :param df:
    :param clf:
    :return:
    """
    clf = clone(clf)
    clf.fit(x, y)

    groups = list(df.index.get_level_values(0))
    cv = GroupKFold(n_splits=3).split(x, y, groups)
    score = cross_val_score(clf, x, y, cv=cv).mean()
    return adjust_r2(score, x.shape[0], x.shape[1])
