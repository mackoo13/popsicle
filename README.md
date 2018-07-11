# Wombat

## Outline

We want to predict a loop execution time based on PAPI performance counters.

The general procedure is as follows:

#### C part
1. Generate and compile the code for different loop bounds (e.g. repeating some operation 100, 200, 300... times).
2. Execute the loop for each parameter and collect PAPI counter values.
3. Repeat this for several loops, accumulating the results (PAPI output + execution time) in a CSV file.

For more details, see `collect_multiplexing.sh` and `exec_loop_multiplexing.c`

#### Python part (ML)
1. PAPI output will be the input vector. We want to train a model to predict the execution time.
2. Get rid of large numbers by [scaling](http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) each feature independently. This is needed because SVR is not able to process very large values.
3. Reduce the number of dimensions using [PCA](http://scikit-learn.org/stable/modules/decomposition.html#pca) (also, to allow effcient use of SVR).
4. Use [SVR](http://scikit-learn.org/stable/modules/svm.html) to train the regression model to predict the execution time.

For more details, see `python/ml-multiplex.ipynb`
