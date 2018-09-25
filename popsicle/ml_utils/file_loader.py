import os
import pandas as pd
from typing import List
from popsicle.ml_utils.data import Data
from popsicle.ml_utils.df_utils import df_aggregate, df_sort_cols, df_scale_by_tot_ins, get_df_meta
from popsicle.utils import check_config

check_config(['OUT_DIR'])
out_dir = os.path.abspath(os.environ['OUT_DIR'])
min_time = 100


class FileLoader:
    def __init__(self, files, mode='gcc', dim=None, scaler=None):
        if mode in ('predict', 'p') and scaler is None:
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
        self.df = None
        self.df_meta = get_df_meta()

        if mode in ('time', 't'):
            self.load = self.load_time
            self.mode = 'time'
        elif mode in ('gcc', 'g'):
            self.load = self.load_gcc
            self.mode = 'gcc'
        elif mode in ('unroll', 'u'):
            self.load = self.load_unroll
            self.mode = 'unroll'
        elif mode in ('predict', 'p'):
            self.load = self.load_predict
            self.mode = 'predict'
        else:
            raise Exception('Unknown feature selection mode')
            
        self.load()

        if self.mode == 'predict':
            self.data.scale_full()

    def load_time(self):
        df = self.__csv_to_df()

        self.__df_add_metadata()
        self.__df_filter_by_min_time('time')
        self.__df_sort_cols()

        self.data = Data(self.mode, df, self.scaler)

    def load_gcc(self):
        df_o0 = self.__csv_to_df(name_suffix='_O0')
        df_o3 = self.__csv_to_df(name_suffix='_O3', cols=['alg', 'run', 'time_O3'])
        self.df = df_o0.merge(df_o3, left_index=True, right_index=True)

        self.__df_filter_by_min_time('time_O3')
        self.__df_scale_by_tot_ins()
        self.__df_add_speedup_col('time_O0', 'time_O3')
        self.__df_add_metadata()
        self.__df_sort_cols()

        self.data = Data(self.mode, self.df, self.scaler)

    def load_unroll(self):
        df_nour = self.__csv_to_df(name_suffix='_nour')
        df_ur = self.__csv_to_df(name_suffix='_ur', cols=['alg', 'run', 'time_ur'])
        self.df = df_nour.merge(df_ur, left_index=True, right_index=True)

        self.__df_add_metadata()
        self.__df_filter_by_min_time('time_ur')
        self.__df_scale_by_tot_ins()
        self.__df_add_speedup_col('time_nour', 'time_ur')
        self.__df_sort_cols()

        self.data = Data(self.mode, self.df, self.scaler)

    def load_predict(self):
        df = self.__csv_to_df()

        if any(df['time'] < min_time):
            raise ValueError('Execution time should be at leat 100ms to perform prediction!')

        df = df_sort_cols(df)
        self.data = Data(self.mode, df, self.scaler)

    # PRIVATE MEMBERS

    def __df_add_metadata(self):
        for col in self.df_meta.columns:
            if col != 'alg':
                self.df[col] = self.df.index.get_level_values(0)
                self.df[col] = self.df[col].apply(lambda alg: self.__get_metadata(alg, col))

                if self.dim is not None:
                    self.df = self.df.loc[self.df[col].isin(self.dim)]

    def __df_add_speedup_col(self, col_before, col_after):
        self.df['speedup'] = self.df[col_before] / self.df[col_after]

    def __df_filter_by_min_time(self, col_name):
        self.df = self.df.loc[self.df[col_name] >= min_time]

    def __df_scale_by_tot_ins(self):
        self.df = df_scale_by_tot_ins(self.df)

    def __df_sort_cols(self):
        self.df = df_sort_cols(self.df)

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

    def __get_metadata(self, alg: str, col: str):
        try:
            return self.df_meta.loc[alg, col]
        except KeyError:
            return -1
