# Code transformation

Scripts `popsicle-transform-lore`, `popsicle-transform-lore-unroll` and `popsicle-transform-pips` prepare C source code to be executed and to perform measurements with PAPI.

The input is meant to be in a format used in LORE.


## Prerequisites

_Previous step: [source code download](01_lore_download.md)_

Remember to run `source config/lore.cfg`. It will populate following environment variables:

- `LORE_ORIG_PATH` - original LORE programs (input)
- `PIPS_ORIG_PATH` - original PIPS programs (input)
- `LORE_PROC_PATH` - output directory for `popsicle-transform-lore`
- `LORE_PROC_CLANG_PATH` - output directory for `popsicle-transform-lore-unroll`
- `PIPS_PROC_PATH` - output directory for `popsicle-transform-pips`


## Usage (LORE programs)

`popsicle-transform-lore`

The input code is expected to be in the format used in LORE repository.

* Inserts PAPI instructions in places indicated by `#pragma scop` and `#pragma endscop`
* Attempts to generate array allocation and initialisation code, which is missing in LORE

### Example
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
    #include "/home/maciej/ftb/popsicle/papi/papi_utils.h"
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


## Usage (LORE programs with loop unrolling)

`popsicle-transform-lore-unroll`

The effect of this script is the same as of `popsicle-transform-lore-unroll`. Besides, it inserts a `#pragma` statement above the innermost loop.

TODO list possible options for unrolling

The output code is meant to be compiled with Clang (see more about its [unrolling support](https://clang.llvm.org/docs/AttributeReference.html#pragma-unroll-pragma-nounroll)).

#### Example
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
    for (i = 0; i < n; i++) {
      #pragma unroll
      for (j = 0; j < n; j++) {
        x[i][j] = j + 42 * i;
      }
    }
    ...


## Next step

Once your programs are transformed, you can [generate the parameters](03_parameters_generation.md) and run them.
