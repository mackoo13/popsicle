# Code transformation

Scripts `popsicle-transform-lore`, `popsicle-transform-lore-unroll` and `popsicle-transform-pips` prepare C source code to be executed and to perform measurements with PAPI.

The input is meant to be in a format used in LORE.


## Prerequisites

_Previous step: [source code download](01_lore_download.md)_

Remember to run `source config/lore.cfg`. It will populate following environment variables:

- `LORE_ORIG_PATH` - original LORE programs (input)
- `LORE_PROC_PATH` - output directory for `popsicle-transform-lore`
- `LORE_PROC_CLANG_PATH` - output directory for `popsicle-transform-lore-unroll`


## Usage

`popsicle-transform-lore [-u] [-v]`

The input code (in `LORE_ORIG_PATH`) is expected to be in the format used in LORE repository. This command:

* Inserts PAPI instructions in places indicated by `#pragma scop` and `#pragma endscop`
* Attempts to generate array allocation and initialisation code, which is missing in LORE
* If `-u` is specified, it also inserts a `#pragma` statement above the innermost loop. The mode of unrolling (e.g. `unroll` or `nounroll`) can be provided on compilation time (see Example 2).
* `-v` enables verbose mode.


### Example 1 (without loop unrolling)

Before:

    #include <stdio.h>
    #include <stdlib.h>
    extern int i;
    extern int n;
    extern double *x;
    
    void loop()
    {
    #pragma scop
    
        for(i = 0; i < n; i++) {
            x[i] = 42 * i;
        }
    
    #pragma endscop
    }

After:

    #include <stdio.h>
    #include <stdlib.h>
    #include <papi.h>
    #include <time.h>
    #include "/my/path/to/papi_utils.h"
    #define MAX(x, y) (((x) > (y)) ? (x) : (y))
    int i;
    double *x;
    void loop(int set, long_long* values, clock_t* begin, clock_t* end)
    {
      n = PARAM_N;
      
      x = malloc((n + 2) * sizeof(double));
      for (int i_0 = 0; i_0 < n; i_0 ++ )
      {
        x[i_0] = (double) rand();
      }
    
      exec(PAPI_start(set));
      *begin = clock();
      #pragma scop
      for (i = 0; i < n; i++)
      {
        x[i] = 1 + 42 * i;
      }
    
      #pragma endscop
      *end = clock();
      exec(PAPI_stop(set, values));
    }    


#### Example 2 (loop unrolling)

Before:

    ...
    for(i = 0; i < n; i++) {
      for (j = 0; j < n; j++) {
        x[i][j] = j + 42 * i;
      }
    }
    ...

After:

    ...
    #define PRAGMA(p) _Pragma(p)
    ...
    for (i = 0; i < n; i++) {
      PRAGMA(PRAGMA_UNROLL)
      for (j = 0; j < n; j++) {
        x[i][j] = j + 42 * i;
      }
    }
    ...

You can select the mode of unrolling on compilation time by specifying the `PRAGMA_UNROLL` parameter - for example:

    gcc -D PRAGMA_UNROLL=nounroll
    
will generate

    #pragma nounroll

## Next step

Once your programs are transformed, you can [generate the parameters](03_parameters_generation.md) and run them.
