import os

import pandas as pd
from sklearn.preprocessing import RobustScaler
from random import shuffle


if 'PAPI_OUT_DIR' not in os.environ:
    print('Invalid config')
    exit(1)

out_dir = os.environ['PAPI_OUT_DIR']


def aggregate(df):
    return df.groupby(['alg', 'run'])[df.columns[2:]].min()


def scale_by_tot_ins(df):
    for col in df.columns:
        if col[:4] == 'PAPI' and col != 'PAPI_TOT_INS':
            df[col] = df[col].astype(float).div(df['PAPI_TOT_INS'], axis=0)
    df['PAPI_TOT_INS'] = 1
    df = df.dropna()
    return df


def df_train_test_split(df, test_split=0.3):
    algs = list(set(df.index.get_level_values(0)))
    shuffle(algs)
    split_point = int(test_split * len(algs))
    algs_test = algs[:split_point]

    test_mask = [a in algs_test for a in df.index.get_level_values(0)]
    train_mask = [not q for q in test_mask]
    df_test = df.loc[test_mask]
    df_train = df.loc[train_mask]
    return df_train, df_test


def df_sort_cols(df):
    cols = sorted(list(df.columns.values))
    return df[cols]


def df_to_xy(df, drop_cols, y_col):
    x = df.drop(drop_cols, axis=1).values
    y = df[y_col].values
    return x, y


def get_df_meta():
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

    def csv_to_df(self, name_suffix='', cols=None):
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

        self.x_train, self.y_train = df_to_xy(self.df_train, ['time'], 'time')
        self.x_test, self.y_test = df_to_xy(self.df_test, ['time'], 'time')

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

        self.x_train, self.y_train = df_to_xy(self.df_train, ['time_O0', 'time_O3', 'speedup', 'max_dim'], 'speedup')
        self.x_test, self.y_test = df_to_xy(self.df_test, ['time_O0', 'time_O3', 'speedup', 'max_dim'], 'speedup')

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

        self.x_train, self.y_train = df_to_xy(self.df_train, ['time_ur', 'time_nour', 'speedup', 'max_dim'], 'speedup')
        self.x_test, self.y_test = df_to_xy(self.df_test, ['time_ur', 'time_nour', 'speedup', 'max_dim'], 'speedup')

        self.scale()

    def load_conv(self):
        df = self.csv_to_df()

        df = df.loc[df['time'] > 100]
        df = scale_by_tot_ins(df)

        algs = list(df.index.get_level_values(0))
        df = df_sort_cols(df)
        df['dims'] = [q.split('_')[0][1:] for q in algs]
        df['rev'] = [q.split('_')[1][1:] for q in algs]

        self.df = df

    def split_conv(self):
        self.df_train, self.df_test = df_train_test_split(self.df)

        self.x_train, self.y_train = df_to_xy(self.df_train, ['dims'], 'rev')
        self.x_test, self.y_test = df_to_xy(self.df_test, ['dims'], 'rev')

        self.scale()
