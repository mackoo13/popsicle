// https://vectorization.computer/loop.html?id=65c08473-5826-484a-878d-1043040ac102&benchmark=cortexsuite&version=default&application=clustering-spectral&file=spectral.c&func=get_k_data&line=43

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <papi.h>
#include "../../papi_utils/papi_events.h"

int i;
int k;
double min;
int j;
int n;
int * check;
double * ev;
int index2;
int l;
double ** k_data;
double * A;

int loop(int set, long_long* values)
{
    k = K;
    n = N;

    check = malloc(n * sizeof(int));
    ev = malloc(n * sizeof(double));
    A = malloc((n*n+n+1) * sizeof(double));

    k_data = malloc(n * sizeof(double));
    for (int q = 0; q < n; ++q) {
        k_data[q] = malloc(k * sizeof(double));
    }

#pragma scop
    exec(PAPI_start(set));

    for(i = 0; i < k; i++)
    {
        min = 1.7976931348623157e+308;
        for(j = 0; j < n; j++)
        {
            if(check[j]) continue;
            else
            {
                if(ev[j] < min)
                {
                    min = ev[j];
                    index2 = j;
                }
            }
        }
        check[index2] = 1;
        for(l = 0; l < n; l++) k_data[l][i] = A[l * n + index2];
    }

    exec(PAPI_stop(set, values));
#pragma endscop
}
