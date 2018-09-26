from sklearn.preprocessing import RobustScaler
from popsicle.ml_utils.df_utils import df_to_xy, df_train_test_split


class Data:
    def __init__(self, mode, df, scaler=None):
        if mode in ('time', 't'):
            self.mode = 'time'
            self.drop_cols = ['max_arr_dim', 'loop_depth']
            self.y_col = 'time'
        elif mode in ('gcc', 'g'):
            self.mode = 'gcc'
            self.drop_cols = ['time_O0', 'time_O3', 'max_arr_dim', 'loop_depth']
            self.y_col = 'speedup'
        elif mode in ('unroll', 'u'):
            self.mode = 'unroll'
            self.drop_cols = ['time_ur', 'time_nour', 'max_arr_dim', 'loop_depth']
            self.y_col = 'speedup'
        elif mode in ('predict', 'p'):
            self.mode = 'predict'
            self.drop_cols = []
            self.y_col = 'time'
        else:
            raise Exception('Unknown mode')

        self.full_set = df_to_xy(df, self.drop_cols, self.y_col)
        self.train_set = None
        self.test_set = None

        self.df = df
        self.scaler = scaler

    def scale_full(self):
        self.full_set.x.update(
            self.scaler.transform(self.full_set.x)
        )

    def scale_train_test(self) -> None:
        """
        Scales each column of data.
        See http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html for more details.
        """
        self.scaler = RobustScaler(quantile_range=(10, 90))
        self.train_set.x.update(
            self.scaler.fit_transform(self.train_set.x)
        )
        self.test_set.x.update(
            self.scaler.transform(self.test_set.x)
        )

        print('Train set:', self.train_set.x.shape)
        print('Test set: ', self.test_set.x.shape)

    def split(self) -> None:
        df_train, df_test = df_train_test_split(self.df)

        self.train_set = df_to_xy(df_train, self.drop_cols, self.y_col)
        self.test_set = df_to_xy(df_test, self.drop_cols, self.y_col)

        self.scale_train_test()
