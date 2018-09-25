# Performance Counters

Performance counters are statistics about program execution collected by the processor. They include mainly numbers of instructions of certain kinds.


Popsicle uses [PAPI](http://icl.utk.edu/papi/) library to perform these measurements in C programs.


## Available events

The set of available events might depend on your architecture. For more information, refer to [PAPI events list](http://icl.cs.utk.edu/projects/papi/presets.html).


## Multiplexing

PAPI is only able to collect data for a couple of events at the same time (the exact number is architecture-dependent).

To obtain more events, Popsicle uses [multiplexing](http://icl.cs.utk.edu/projects/papi/wiki/Multiplexing). In this mode, PAPI switches between different events during execution and returns approximate results. Of course, loss of precision is inevitable when using this strategy - especially when a program runs for a short time. 

In this project, all data with short execution time (typically under 100ms) is discarded as unreliable duo to the loss of precision. Thus, also prediction can only be accurate for programs which execute long enough.


## Application in prediction

Performance counters are always measured _before_ performing the optimisation, both during training and prediction.


## Reference

>Terpstra, D., Jagode, H., You, H., Dongarra, J. "Collecting Performance Data with PAPI-C", Tools for High Performance Computing 2009, Springer Berlin / Heidelberg, 3rd Parallel Tools Workshop, Dresden, Germany, pp. 157-173, 2010.