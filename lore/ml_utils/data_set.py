class DataSet:
    def __init__(self, x=None, y=None, df=None, x_labels=None):
        if x is None:
            x = []

        if y is None:
            y = []

        self.x = x
        self.y = y
        self.df = df
        self.x_labels = x_labels

    def copy(self):
        return DataSet(self.x, self.y, self.df, self.x_labels)
