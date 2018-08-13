## Code format

In order to collect the PAPI measurements and make predictions about speedup or execution time, the code provided by the user must follow specific format.

The code structure is based on files from LORE repository. It should contain:
* `void loop()` function, which will be called by Wombat during execution. Other functions can also be defined if they are called inside `loop`.
* `#pragma scop` and `#pragma endscop` enclosing the loop kernel.

```$xslt
// includes
// variables and arrays declaration

void loop()
{
    #pragma scop

    // loop kernel to be measured

    #pragma endscop
}
```


### Example

```$xslt
#include <stdio.h>
#include <stdlib.h>
int N;
int* A;

void loop()
{

    N = 42;
    A = malloc(nr * sizeof(int));

    #pragma scop
    
    for(int i = 0; i < N; i++)
        A[i] += i;
            
    #pragma endscop
}
```