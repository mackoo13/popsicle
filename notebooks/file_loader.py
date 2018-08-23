import os

import pandas as pd
from sklearn.preprocessing import RobustScaler
from random import shuffle

out_dir = '~/ftb/papi_output/'


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
    def __init__(self, files, mode='speedup', scaler=None, dim={1, 2}):
        self.x = []
        self.x_test = []
        self.y = []
        self.y_test = []
        self.df = None
        self.df_test = None
        self.files = files
        self.scaler = scaler
        self.dim = list(dim)
        self.mode = mode
        
        if mode == 'time':
            self.load = self.load_time
        elif mode == 'speedup':
            self.load = self.load_speedup
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

    def csv_to_df(self, name_suffix='', cols=None):
        paths = [os.path.join(out_dir, self.mode, p) for p in self.files]

        dfs = [pd.read_csv(path + name_suffix + '.csv', error_bad_lines=False) for path in paths]
        df = pd.concat(dfs)
        df['run'] = df['run'].astype(str)

        if cols is not None:
            df = df[cols]

        df = aggregate(df)
        print('Loaded dataframe:', df.shape)

        return df

    def load_time(self, scaler=None):
        df = self.csv_to_df()

        # df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')  # todo
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time'] > 10]
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)

        self.df, self.df_test = df_train_test_split(df)

        x, y = df_to_xy(self.df, ['time'], 'time')
        x_test, y_test = df_to_xy(self.df_test, ['time'], 'time')

        if self.scaler is None:
            scaler = RobustScaler(quantile_range=(10, 90))
            self.x = scaler.fit_transform(x)
            self.scaler = scaler
        else:
            self.x = scaler.transform(x)

        self.x_test = scaler.transform(x_test)
        self.y = y
        self.y_test = y_test

        print('Train:', self.df.shape)
        print('Test: ', self.df_test.shape)

    def load_speedup(self, scaler=None):
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

        self.df, self.df_test = df_train_test_split(df)

        x, y = df_to_xy(self.df,['time_O0', 'time_O3', 'speedup', 'max_dim'], 'speedup')
        x_test, y_test = df_to_xy(self.df_test,['time_O0', 'time_O3', 'speedup', 'max_dim'], 'speedup')

        if self.scaler is None:
            scaler = RobustScaler(quantile_range=(10, 90))
            self.x = scaler.fit_transform(x)
            self.scaler = scaler
        else:
            self.x = scaler.transform(x)

        self.x_test = scaler.transform(x_test)
        self.y = y
        self.y_test = y_test

        print('Train:', self.df.shape)
        print('Test: ', self.df_test.shape)
