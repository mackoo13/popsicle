import os
import pandas as pd
from typing import List

from ml_utils.data import Data
from ml_utils.df_utils import df_aggregate, df_sort_cols, df_scale_by_tot_ins, get_df_meta
from utils import check_config

check_config(['PAPI_OUT_DIR', 'LORE_PROC_PATH'])
out_dir = os.environ['PAPI_OUT_DIR']


class FileLoader:
    def __init__(self, files, mode='speedup', purpose='train', dim={1, 2}, scaler=None):
        if purpose not in ('train', 'predict'):
            raise ValueError('Parameter \'purpose\' must be either \'train\' or \'predict\'.')

        if purpose == 'predict' and scaler is None:
            raise ValueError('Scaler must be provided to make predictions')

        self.data = None

        self.files = files
        self.dim = dim
        self.scaler = scaler
        self.purpose = purpose

        if mode in ('time', 't'):
            self.load = self.load_time
            self.mode = 'time'
        elif mode in ('speedup', 's'):
            self.load = self.load_speedup
            self.mode = 'speedup'
        elif mode in ('unroll', 'u'):
            self.load = self.load_unroll
            self.mode = 'unroll'
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

        if purpose == 'predict':
            self.data.scale_full()
        else:
            self.data.split()

    # PRIVATE MEMBERS

    def __csv_to_df(self, name_suffix: str= '', cols: List[str]=None) -> pd.DataFrame:
        """
        Loads csv file(s) to a DataFrame
        :param name_suffix: Suffix which will be added to each file name. For example, in 'speedup' mode it can load
            file_name_O0.csv and file_name_O3.csv.
        :param cols: Which columns to load
        :return: DataFrame
        """
        paths = [os.path.join(out_dir, self.mode, p) for p in self.files]

        dfs = [pd.read_csv(path + name_suffix + '.csv', error_bad_lines=False) for path in paths]
        df = pd.concat(dfs, join='inner')
        df['run'] = df['run'].astype(str)

        if cols is not None:
            df = df[cols]

        df = df_aggregate(df)
        print('Loaded dataframe:', df.shape)

        return df

    def load_time(self):
        df = self.__csv_to_df()

        # df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')  # todo
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time'] > 10]
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)

    def load_speedup(self):
        df_o0 = self.__csv_to_df(name_suffix='_O0')
        df_o3 = self.__csv_to_df(name_suffix='_O3', cols=['alg', 'run', 'time_O3'])
        df = df_o0.merge(df_o3, left_index=True, right_index=True)

        df_meta = get_df_meta()
        df['max_dim'] = df.index.get_level_values(0)
        df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_O3'] > 10]
        df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_scale_by_tot_ins(df)

        df['speedup'] = df['time_O0'] / df['time_O3']

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)

    def load_unroll(self):
        df_nour = self.__csv_to_df(name_suffix='_nour')
        df_ur = self.__csv_to_df(name_suffix='_ur', cols=['alg', 'run', 'time_ur'])
        df = df_nour.merge(df_ur, left_index=True, right_index=True)

        df_meta = get_df_meta()
        df['max_dim'] = df.index.get_level_values(0)
        df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_ur'] > 10]
        df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_scale_by_tot_ins(df)

        df['speedup'] = df['time_nour'] / df['time_ur']

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)
