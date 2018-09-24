import os
import pandas as pd
from typing import List
from popsicle.ml_utils.data import Data
from popsicle.ml_utils.df_utils import df_aggregate, df_sort_cols, df_scale_by_tot_ins, get_df_meta
from popsicle.utils import check_config

check_config(['OUT_DIR', 'LORE_PROC_PATH'])
out_dir = os.environ['OUT_DIR']


class FileLoader:
    def __init__(self, files, mode='gcc', dim={1, 2}, scaler=None):
        if mode == 'input' and scaler is None:
            raise ValueError('Scaler must be provided to make predictions')

        self.data = None

        self.files = []
        for file in files:
            if file.endswith('.csv'):
                print('Warning: ' + file.split('/')[-1] + ' interpreted as ' + file.split('/')[-1][:-4] +
                      ' (file names should be provided without extensions).')
                self.files.append(file[:-4])
            else:
                self.files.append(file)

        self.dim = dim
        self.scaler = scaler

        if mode in ('time', 't'):
            self.load = self.load_time
            self.mode = 'time'
        elif mode in ('gcc', 'g'):
            self.load = self.load_gcc
            self.mode = 'gcc'
        elif mode in ('unroll', 'u'):
            self.load = self.load_unroll
            self.mode = 'unroll'
        elif mode in ('input', 'i'):
            self.load = self.load_input
            self.mode = 'input'
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

        if self.mode == 'input':
            self.data.scale_full()


    # PRIVATE MEMBERS

    def __csv_to_df(self, name_suffix: str= '', cols: List[str]=None) -> pd.DataFrame:
        """
        Loads csv file(s) to a DataFrame
        :param name_suffix: Suffix which will be added to each file name. For example, in 'gcc' mode it can load
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
        df = df.loc[df['time'] > 100]
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)

    def load_gcc(self):
        df_o0 = self.__csv_to_df(name_suffix='_O0')
        df_o3 = self.__csv_to_df(name_suffix='_O3', cols=['alg', 'run', 'time_O3'])
        df = df_o0.merge(df_o3, left_index=True, right_index=True)

        # df_meta = get_df_meta()
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        df = df.loc[df['time_O3'] > 100]
        # df = df.loc[df['max_dim'].isin(self.dim)]

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

    def load_input(self):
        df = self.__csv_to_df()

        # df_meta = pd.read_csv('/home/maciej/ftb/kernels_lore/proc/metadata.csv', index_col='alg')  # todo
        # df['max_dim'] = df.index.get_level_values(0)
        # df['max_dim'] = df['max_dim'].apply(lambda q: df_meta.loc[q]['max_dim'])
        # df = df.loc[df['time'] > 100]     # todo
        # df = df.loc[df['max_dim'].isin(self.dim)]

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)
