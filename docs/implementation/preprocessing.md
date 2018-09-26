# Preprocessing

## Aggregating repeated measurements

If one program has been executed multiple times for the same parameters, we only preserve the _minimal_ value of each feature. 

Any noise (for example caused by other programs running in the system) can only add to the performance counters - this is why we expect the minimum to be closest to the true theoretical performance of the program.


## Discarding short executions

Loss of precision with PAPI multiplexing is most visible in short-running programs. Many features have values as low as 0, because PAPI had no time to measure all events.

Thus, all samples with execution time below given time limit (by default, 100ms) are discarded.

Note that to obtain a reliable score from prediction, the predicted program must also fulfil this condition.


## Normalisation

All PAPI events are normalised by dividing their value by the total number of instructions. This way we prevent  them from being dependent on length of execution.

Experiments show that for many programs, PAPI events after normalisation are indeed independent of loop bounds.

This approach has been inspired by "Rapidly Selecting Good Compiler Optimizations using Performance Counters", J. Cavazos et al.


## Standardisation

To ensure that all features have a similar magnitude and, preferably, a normal-like distribution (which is required by many ML models), each feature is scaled independently by [RobustScaler](http://scikit-learn.org/stable/modules/preprocessing.html#scaling-data-with-outliers).


## Outliers

The outliers are not removed due to insufficient amount of samples to detect them. However, the outliers are skipped when training the RobustScaler (see Standardisation section above).
