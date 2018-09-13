import os
from typing import Tuple, List
from random import shuffle
import pandas as pd
import numpy as np
from utils import check_config

check_config(['LORE_PROC_PATH'])
proc_dir = os.environ['LORE_PROC_PATH']


class DataSet:
    def __init__(self, x=None, y=None, df=None, x_labels=None):
        if x is None:
            x = []

        if y is None:
            y = []

        self.x = x
        self.y = y
        self.df = df
        self.x_labels = x_labels

    def copy(self):
        return DataSet(self.x, self.y, self.df, self.x_labels)


def df_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Of all measurements of the same program with same parameters, take the minimum.
    Minimum should be always the best approximation of the actual program characteristics without any overhead.
    """
    return df.groupby(['alg', 'run']).min()


def df_get_index_col(df: pd.DataFrame, col: str) -> List:
    """
    todo
    """
    col_level = df.index.names.index(col)
    return df.index.get_level_values(col_level)


def df_scale_by_tot_ins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Divides values of all PAPI values outputs by PAPI_TOT_INS in order to normalise them
    """
    for col in df.columns:
        if col[:4] == 'PAPI' and col != 'PAPI_TOT_INS':
            df[col] = df[col].astype(float).div(df['PAPI_TOT_INS'], axis=0)
    df['PAPI_TOT_INS'] = 1
    df = df.dropna()
    return df


def df_sort_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts the columns of a DataFrame (by column name)
    """
    cols = sorted(list(df.columns.values))
    return df[cols]


def df_to_xy(df: pd.DataFrame, drop_cols: List[str], y_col: str) -> DataSet:
    """
    Separates ML input (x) and output (y) in a DataFrame
        drop_cols: Columns to remove from df
        y_col: Output column (skipped in x, included in y)
    """
    y = df[y_col].values
    df = df.drop(drop_cols, axis='columns')
    df_x = df.drop([y_col], axis='columns')
    x = df_x.values
    x_labels = np.array(df_x.columns)
    return DataSet(x, y, df, x_labels)


def df_train_test_split(df: pd.DataFrame, test_split: float=0.3) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame into training and testing data. All executions of one program are guaranteed to be in the same
    partition (this ensures that training and testing data are in fact distinct).
        test_split: fraction from [0, 1]: part of data to be selected as test set
    """
    algs = list(set(df_get_index_col(df, 'alg')))
    shuffle(algs)
    split_point = int(test_split * len(algs))
    algs_test = algs[:split_point]

    test_mask = [a in algs_test for a in df_get_index_col(df, 'alg')]
    train_mask = [not q for q in test_mask]
    df_test = df.loc[test_mask]
    df_train = df.loc[train_mask]
    return df_train, df_test


def get_df_meta() -> pd.DataFrame:
    """
    Loads metadata to a DataFrame, which then can be merged with the rest of data.
    """
    return pd.read_csv(os.path.join(proc_dir, 'metadata.csv'), index_col='alg')
