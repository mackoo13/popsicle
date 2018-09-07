import os
from typing import Tuple, List

import pandas as pd
from sklearn.preprocessing import RobustScaler
from random import shuffle


if 'PAPI_OUT_DIR' not in os.environ:
    raise EnvironmentError

out_dir = os.environ['PAPI_OUT_DIR']


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(['alg', 'run']).min()


def aggregate_conv_rev(df: pd.DataFrame) -> pd.DataFrame:
    df = df.groupby(['dims', 'n_arrays', 'rev']).mean()
    rev_level = df.index.names.index('rev')

    for index, row in df.iterrows():
        if index[rev_level]:
            row0_index = list(index)
            row0_index[rev_level] = False
            row0 = df.loc[tuple(row0_index), :]
            df.loc[index] = row / row0        # todo 0

    df = df.drop(False, level=2)

    df.index = df.index.droplevel(2)
    return df


def print_mean_and_std(df: pd.DataFrame) -> None:
    for col in df.columns:
        vals = df[col]
        print(col, '\t', str(round(vals.mean(), 2)) + '+/-' + str(round(vals.std(), 2)))


def remove_unpaired_rev(df: pd.DataFrame) -> pd.DataFrame:
    for index, row in df.iterrows():
        if not (
                (df['dims'] == row['dims']) &
                (df['n_arrays'] == row['n_arrays']) &
                (df['rev'] != row['rev']) &
                (df.index.get_level_values(1) == index[1])
        ).any():
            df = df.drop(index)
            print(index)

    return df


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
    todo
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
    Sorts the columns of a DataFrame
    """
    cols = sorted(list(df.columns.values))
    return df[cols]


def df_to_xy(df: pd.DataFrame, drop_cols: List[str], y_col: str) -> Tuple[any, any, pd.DataFrame]:  # todo types
    """
    todo
    :param df:
    :param drop_cols:
    :param y_col:
    :return:
    """
    if y_col not in drop_cols:
        drop_cols.append(y_col)

    y = df[y_col].values
    df = df.drop(drop_cols, axis=1)
    x = df.values
    return x, y, df


def get_df_meta():
    """
    todo
    :return:
    """
    if 'LORE_PROC_PATH' not in os.environ:
        raise EnvironmentError

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
            self.split = self.split_time
            self.mode = 'time'
        elif mode in ('speedup', 's'):
            self.load = self.load_speedup
            self.split = self.split_speedup
            self.mode = 'speedup'
        elif mode in ('unroll', 'u'):
            self.load = self.load_unroll
            self.split = self.split_unroll
            self.mode = 'unroll'
        elif mode in ('conv', 'c'):
            self.load = self.load_conv
            self.split = self.split_conv
            self.mode = 'conv'
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

    def csv_to_df(self, name_suffix: str='', cols: List[str]=None):
        """
        todo
        :param name_suffix:
        :param cols:
        :return:
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

    def scale(self):
        """
        todo
        :return:
        """
        scaler = RobustScaler(quantile_range=(10, 90))
        self.x_train = scaler.fit_transform(self.x_train)
        self.x_test = scaler.transform(self.x_test)

        print('Train:', self.df_train.shape)
        print('Test: ', self.df_test.shape)

    def load_time(self):
        df = self.csv_to_df()

        # df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')  # todo
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time'] > 10]
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)
        self.df = df

    def split_time(self):
        self.df_train, self.df_test = df_train_test_split(self.df)

        drop_cols = []
        y_col = 'time'
        self.x_train, self.y_train, self.df_train = df_to_xy(self.df_train, drop_cols, y_col)
        self.x_test, self.y_test, self.df_test = df_to_xy(self.df_test, drop_cols, y_col)

        self.scale()

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

    def split_speedup(self):
        self.df_train, self.df_test = df_train_test_split(self.df)

        drop_cols = ['time_O0', 'time_O3', 'max_dim']
        y_col = 'speedup'
        self.x_train, self.y_train, self.df_train = df_to_xy(self.df_train, drop_cols, y_col)
        self.x_test, self.y_test, self.df_test = df_to_xy(self.df_test, drop_cols, y_col)

        self.scale()

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

    def split_unroll(self):
        self.df_train, self.df_test = df_train_test_split(self.df)

        drop_cols = ['time_ur', 'time_nour', 'max_dim']
        y_col = 'speedup'
        self.x_train, self.y_train, self.df_train = df_to_xy(self.df_train, drop_cols, y_col)
        self.x_test, self.y_test, self.df_test = df_to_xy(self.df_test, drop_cols, y_col)

        self.scale()

    def load_conv(self):
        df = self.csv_to_df()

        df = df.loc[df['time'] > 100]
        df = scale_by_tot_ins(df)

        algs = list(df.index.get_level_values(0))
        df = df_sort_cols(df)
        df['dims'] = [q.split('_')[0][1:] for q in algs]
        df['dims'] = df['dims'].astype(int)
        df['rev'] = [q.split('_')[1][1:] for q in algs]
        df['rev'] = df['rev'].apply(lambda v: v == '1').astype(bool)
        df['n_arrays'] = [q.split('_')[2][1:] for q in algs]
        df['n_arrays'] = df['n_arrays'].astype(int)

        df = remove_unpaired_rev(df)
        df = aggregate_conv_rev(df)

        self.df = df

    def split_conv(self):
        self.df_train, self.df_test = df_train_test_split(self.df)

        drop_cols = ['dims', 'time', 'n_arrays']
        y_col = 'rev'
        self.x_train, self.y_train, self.df_train = df_to_xy(self.df_train, drop_cols, y_col)
        self.x_test, self.y_test, self.df_test = df_to_xy(self.df_test, drop_cols, y_col)

        self.scale()
