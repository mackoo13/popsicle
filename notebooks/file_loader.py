import pandas as pd
from sklearn.preprocessing import RobustScaler
from random import shuffle

out_dir = '~/ftb/papi_output/speedup/'


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
    algs_train = algs[split_point:]

    test_mask = [a in algs_test for a in df.index.get_level_values(0)]
    train_mask = [not q for q in test_mask]
    df_test = df.loc[test_mask]
    df_train = df.loc[train_mask]
    return df_train, df_test


def df_sort_cols(df):
    cols = sorted(list(df.columns.values))
    return df[cols]


def df_to_xy(df):
    x = df.drop(['time_O0', 'time_O3', 'speedup', 'max_dim'], axis=1).values
    y = df['speedup'].values
    return x, y


class FileLoader:
    def __init__(self, files, scaler=None):
        self.x = []
        self.x_test = []
        self.y = []
        self.y_test = []
        self.df = None
        self.df_test = None
        self.files = files
        self.scaler = scaler

        self.load()

    def load(self, scaler=None):
        paths = [out_dir + p for p in self.files]

        dfs_o0 = [pd.read_csv(path + '_O0.csv', error_bad_lines=False) for path in paths]
        df_o0 = pd.concat(dfs_o0)
        df_o0['run'] = df_o0['run'].astype(str)
        df_o0 = aggregate(df_o0)
        print(df_o0.shape)

        dfs_o3 = [pd.read_csv(path + '_O3.csv', error_bad_lines=False) for path in paths]
        df_o3 = pd.concat(dfs_o3)
        df_o3['run'] = df_o3['run'].astype(str)
        df_o3 = df_o3[['alg', 'run', 'time_O3']]
        df_o3 = aggregate(df_o3)
        print(df_o3.shape)

        df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')

        df = df_o0.merge(df_o3, left_index=True, right_index=True)
        df['max_dim'] = df.index.get_level_values(0)
        df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_O3'] > 0]

        df = scale_by_tot_ins(df)

        df['speedup'] = df['time_O0'] / df['time_O3']

        df = df_sort_cols(df)

        self.df, self.df_test = df_train_test_split(df)

        x, y = df_to_xy(self.df)
        x_test, y_test = df_to_xy(self.df_test)

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
