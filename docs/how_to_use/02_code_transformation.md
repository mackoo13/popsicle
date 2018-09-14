## Code transformation

Scripts `wombat-transform-lore`, `wombat-transform-lore-unroll` and `wombat-transform-pips` prepare C source code to be executed and to perform measurements with PAPI.


### Configuration

Remember to run `source config/lore.cfg` first. It will populate following environment variables:

- `LORE_ORIG_PATH` - original LORE programs (input)
- `PIPS_ORIG_PATH` - original PIPS programs (input)
- `LORE_PROC_PATH` - output directory for `wombat-transform-lore`
- `LORE_PROC_CLANG_PATH` - output directory for `wombat-transform-lore-unroll`
- `PIPS_PROC_PATH` - output directory for `wombat-transform-pips`


### LORE transformation

Usage: `wombat-transform-lore`

Source code: `transform_lore.py`

---

The input code is expected to be in the format used in LORE repository.

* Inserts PAPI instructions in places indicated by `#pragma scop` and `#pragma endscop`
* Attempts to generate array allocation and initialisation code, which is missing in LORE

##### Example
Before:
```$xslt
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
```

After:
```$xslt
#include <stdio.h>
#include <stdlib.h>
#include <papi.h>
#include <time.h>
#include "/home/maciej/ftb/wombat/papi/papi_utils.h"
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

```


### LORE transformation (with loop unrolling)

Usage: `wombat-transform-lore-unroll`

Source code: `transform_lore_unroll.py`

---

This script is a modification of `wombat-transform-lore-unroll`. Besides, it inserts a `#pragma` statement above the innermost loop.

TODO list possible options for unrolling

The output code is meant to be compiled with Clang (see more about its [unrolling support](https://clang.llvm.org/docs/AttributeReference.html#pragma-unroll-pragma-nounroll)).

##### Example
Before:
```$xslt
...
for(i = 0; i < n; i++) {
  for (j = 0; j < n; j++) {
    x[i][j] = j + 42 * i;
  }
}
...
```

After:
```$xslt
...
for (i = 0; i < n; i++) {
  #pragma unroll
  for (j = 0; j < n; j++) {
    x[i][j] = j + 42 * i;
  }
}
...

```


### PIPS transformation

Usage: `wombat-transform-pips`

Source code: `transform_pips.py`

TODO
