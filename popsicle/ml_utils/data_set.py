class DataSet:
    def __init__(self, x=None, y=None):
        if y is None:
            y = []

        self.x = x
        self.y = y

    def copy(self):
        return DataSet(self.x.copy(), self.y)
