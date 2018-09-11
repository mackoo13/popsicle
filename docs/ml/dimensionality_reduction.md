## Dimensionality reduction

### Why?

The advantage of Wombat's dimensionality reduction is twofold:

* It improves the *speed* and *accuracy* of prediction - less features means better computational complexity. Also, it helps us avoid the [curse of dimensionality](http://www.visiondummy.com/2014/04/curse-dimensionality-affect-classification/).
* It's *informative* - after feature selection stage, the algorithm will show which features proved most useful.


### Stages

1. Feature selection
2. Coefficients tuning


### Feature selection

First, the training data is fed to [RandomForestRegressor](http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html). This regressor provides us with a ranking of features ordered by their importance in its prediction.

Using this ranking, we will apply a greedy algorithm to select a group of features:

```$xslt
1. selected_features = []
2. try adding each of the top 5 features to selected_features
3. calculate kNN scores
4. if score(selected_features + best_feature) > score(selected_features):
      selected_features.append(best_feature)
      remove best_feature from ranking
  else:
      remove all 5 features from ranking
5. Repeat 2-4 while ranking is not empty
```

Afterwards, we can run a quick check to make sure none of the features is redundant:

```$xslt
1. Find a feature whose removal increases kNN score
2. Repeat 1 while there are such features
```

In Wombat this usually leads to a reduction from about 50 to 10-20 features. 


### Coefficients tuning

The next step applies a very simple metric learning (todo: link?).

kNN gives us a freedom to choose a non-standard metric for calculating distances between points. In case of this algorithm, we will try to assign optimal weights to each dimension.

For example in two dimensions:

Classical Euclidean distance: `d(a, b) = sqrt((a0 - b0)^2 + (a1 - b1)^2))` 

Weighted Euclidean distance: `d(a, b) = sqrt((w0*a0 - w0*b0)^2 + (w1*a1 - w1*b1)^2))` 

The solution (being a vector of weights: `[w0, w1, ... wn]`) is sought by a genetic algorithm.
