# Training and prediction

By default, Popsicle uses [KNeighborsRegressor](http://scikit-learn.org/stable/modules/neighbors.html#regression) with `distance` metric for prediction.

The optimal value of `n_neighbors` is determined during training.