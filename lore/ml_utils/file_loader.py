import os
import pandas as pd
from typing import Tuple, List
from sklearn.preprocessing import RobustScaler
from random import shuffle

from utils import check_config

check_config(['PAPI_OUT_DIR'])
out_dir = os.environ['PAPI_OUT_DIR']


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Of all measurements of the same program with same parameters, take the minimum.
    Minimum should be always the best approximation of the actual program characteristics without any overhead.
    """
    return df.groupby(['alg', 'run']).min()


def scale_by_tot_ins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Divides values of all PAPI events outputs by PAPI_TOT_INS in order to normalise them
    """
    for col in df.columns:
        if col[:4] == 'PAPI' and col != 'PAPI_TOT_INS':
            df[col] = df[col].astype(float).div(df['PAPI_TOT_INS'], axis=0)
    df['PAPI_TOT_INS'] = 1
    df = df.dropna()
    return df


def df_train_test_split(df: pd.DataFrame, test_split: float=0.3) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame into training and testing data. All executions of one program are guaranteed to be in the same
    partition (this ensures that training and testing data are in fact distinct).
    :param df:
    :param test_split:
    :return:
    """
    algs = list(set(df.index.get_level_values(0)))
    shuffle(algs)
    split_point = int(test_split * len(algs))
    algs_test = algs[:split_point]

    test_mask = [a in algs_test for a in df.index.get_level_values(0)]
    train_mask = [not q for q in test_mask]
    df_test = df.loc[test_mask]
    df_train = df.loc[train_mask]
    return df_train, df_test


def df_sort_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts the columns of a DataFrame (by column name)
    """
    cols = sorted(list(df.columns.values))
    return df[cols]


def df_to_xy(df: pd.DataFrame, drop_cols: List[str], y_col: str) -> Tuple[any, any, pd.DataFrame]:  # todo types
    """
    Separates ML input (x) and output (y) in a DataFrame
    :param df: Input DataFrame
    :param drop_cols: Columns to skip
    :param y_col: Output column
    :return:
    """
    if y_col not in drop_cols:
        drop_cols.append(y_col)

    y = df[y_col].values
    df = df.drop(drop_cols, axis=1)
    x = df.values
    return x, y, df


def get_df_meta() -> pd.DataFrame:
    """
    Loads metadata to a DataFrame, which then can be merged with the rest of data.
    :return: DataFrame
    """
    check_config('LORE_PROC_PATH')

    proc_dir = os.environ['LORE_PROC_PATH']
    return pd.read_csv(os.path.join(proc_dir, 'metadata.csv'), index_col='alg')


class FileLoader:
    def __init__(self, files, mode='speedup', dim={1, 2}):
        self.x_train = []
        self.x_test = []
        self.y_train = []
        self.y_test = []
        self.df = None
        self.df_train = None
        self.df_test = None
        self.files = files
        self.dim = list(dim)

        if mode in ('time', 't'):
            self.load = self.load_time
            self.mode = 'time'
            self.drop_cols = []
            self.y_col = 'time'
        elif mode in ('speedup', 's'):
            self.load = self.load_speedup
            self.mode = 'speedup'
            self.drop_cols = ['time_O0', 'time_O3', 'max_dim']
            self.y_col = 'speedup'
        elif mode in ('unroll', 'u'):
            self.load = self.load_unroll
            self.mode = 'unroll'
            self.drop_cols = ['time_ur', 'time_nour', 'max_dim']
            self.y_col = 'speedup'
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

    def csv_to_df(self, name_suffix: str='', cols: List[str]=None) -> pd.DataFrame:
        """
        Loads csv file(s) to a DataFrame
        :param name_suffix: Suffix which will be added to each file name. Useful when todo
        :param cols: Which columns to load
        :return: DataFrame
        """
        paths = [os.path.join(out_dir, self.mode, p) for p in self.files]

        dfs = [pd.read_csv(path + name_suffix + '.csv', error_bad_lines=False) for path in paths]
        df = pd.concat(dfs, join='inner')
        df['run'] = df['run'].astype(str)

        if cols is not None:
            df = df[cols]

        df = aggregate(df)
        print('Loaded dataframe:', df.shape)

        return df

    def scale(self) -> None:
        """
        Scales each column of data.
        See http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html for more details.
        """
        scaler = RobustScaler(quantile_range=(10, 90))
        self.x_train = scaler.fit_transform(self.x_train)
        self.x_test = scaler.transform(self.x_test)

        print('Train:', self.df_train.shape)
        print('Test: ', self.df_test.shape)

    def split(self) -> None:
        df_train, df_test = df_train_test_split(self.df)

        self.x_train, self.y_train, self.df_train = df_to_xy(df_train, self.drop_cols, self.y_col)
        self.x_test, self.y_test, self.df_test = df_to_xy(df_test, self.drop_cols, self.y_col)

        self.scale()

    def load_time(self):
        df = self.csv_to_df()

        # df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')  # todo
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time'] > 10]
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)
        self.df = df

    def load_speedup(self):
        df_o0 = self.csv_to_df(name_suffix='_O0')
        df_o3 = self.csv_to_df(name_suffix='_O3', cols=['alg', 'run', 'time_O3'])
        df = df_o0.merge(df_o3, left_index=True, right_index=True)

        df_meta = get_df_meta()
        df['max_dim'] = df.index.get_level_values(0)
        df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_O3'] > 10]
        df = df.loc[df['max_dim'].isin(self.dim)]

        df = scale_by_tot_ins(df)

        df['speedup'] = df['time_O0'] / df['time_O3']

        df = df_sort_cols(df)
        self.df = df

    def load_unroll(self):
        df_o0 = self.csv_to_df(name_suffix='_nour')
        df_o3 = self.csv_to_df(name_suffix='_ur', cols=['alg', 'run', 'time_ur'])
        df = df_o0.merge(df_o3, left_index=True, right_index=True)

        df_meta = get_df_meta()
        df['max_dim'] = df.index.get_level_values(0)
        df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_ur'] > 10]
        df = df.loc[df['max_dim'].isin(self.dim)]

        df = scale_by_tot_ins(df)

        df['speedup'] = df['time_nour'] / df['time_ur']

        df = df_sort_cols(df)
        self.df = df
