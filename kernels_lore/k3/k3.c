#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <papi.h>
#include "../../papi_utils/papi_events.h"

int i;
int n;
int j;
double * D;
double * A;

int loop(int set, long_long* values)
{
    n = N;

    D = malloc(n * sizeof(double));
    A = malloc((n*n+n) * sizeof(double));

#pragma scop
    exec(PAPI_start(set));

    for(i = 0; i < n; i++)
    {
        for(j = 0; j < n; j++) D[i] += -A[n * i + j];
        A[n * i + i] = D[i];
    }

    exec(PAPI_stop(set, values));
#pragma endscop
}