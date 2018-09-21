## PAPI

[PAPI](http://icl.utk.edu/papi/) is a library for collecting measurements from performance counters.

>Terpstra, D., Jagode, H., You, H., Dongarra, J. "Collecting Performance Data with PAPI-C", Tools for High Performance Computing 2009, Springer Berlin / Heidelberg, 3rd Parallel Tools Workshop, Dresden, Germany, pp. 157-173, 2010.


### Available events

The set of available events might depend on your architecture. For more information, refer to [PAPI events list](http://icl.cs.utk.edu/projects/papi/presets.html).


### Multiplexing

PAPI is only able to collect data for a couple of events at the same time (the exact number is architecture-dependent).

To obtain more events, Popsicle uses [multiplexing](http://icl.cs.utk.edu/projects/papi/wiki/Multiplexing). In this mode, PAPI switches between different events during execution and returns approximate results. Of course, loss of precision is inevitable when using this strategy - especially when a program runs for a short time. 

In this project, all data with short execution time (typically under 100ms) is discarded to overcome this problem. Thus, prediction is also accurate for such programs only.
