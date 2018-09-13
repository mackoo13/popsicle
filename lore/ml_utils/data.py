import pandas as pd
from sklearn.preprocessing import RobustScaler
from ml_utils.df_utils import df_to_xy, df_train_test_split, DataSet


class Data:
    def __init__(self, mode, df, scaler=None):
        if mode in ('time', 't'):
            self.mode = 'time'
            self.drop_cols = []
            self.y_col = 'time'
        elif mode in ('speedup', 's'):
            self.mode = 'speedup'
            self.drop_cols = ['time_O0', 'time_O3', 'max_dim']
            self.y_col = 'speedup'
        elif mode in ('unroll', 'u'):
            self.mode = 'unroll'
            self.drop_cols = ['time_ur', 'time_nour', 'max_dim']
            self.y_col = 'speedup'
        else:
            raise Exception('Unknown feature selection mode')

        self.full_set = DataSet()
        self.train_set = DataSet()
        self.test_set = DataSet()

        self.scaler = scaler
        self.set_df(df)

    def scale_full(self):
        print('scf')
        self.full_set.x = self.scaler.transform(self.full_set.x)

    def scale_train_test(self) -> None:
        print('sctt')
        """
        Scales each column of data.
        See http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html for more details.
        """
        self.scaler = RobustScaler(quantile_range=(10, 90))
        self.train_set.x = self.scaler.fit_transform(self.train_set.x)
        self.test_set.x = self.scaler.transform(self.test_set.x)

        print('Train:', self.train_set.x.shape)
        print('Test: ', self.test_set.x.shape)

    def set_df(self, df: pd.DataFrame) -> None:
        self.full_set = df_to_xy(df, self.drop_cols, self.y_col)

    def split(self) -> None:
        print('spl')
        df_train, df_test = df_train_test_split(self.full_set.df)

        self.train_set = df_to_xy(df_train, [], self.y_col)
        self.test_set = df_to_xy(df_test, [], self.y_col)

        self.scale_train_test()
