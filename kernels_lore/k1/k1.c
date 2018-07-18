// https://vectorization.computer/loop.html?id=d766ef7f-1c28-4665-95fd-79bd4faf046e&benchmark=cortexsuite&version=default&application=clustering-kmeans&file=kmeans.c&func=k_means&line=109

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <papi.h>
#include "../../papi_utils/papi_events.h"

int i;
int k;
int j;
int m;
double ** c;
int * counts;
double ** c1;

int loop(int set, long_long* values)
{
    k = K;
    m = M;

    c = malloc(k * sizeof(double));
    c1 = malloc(k * sizeof(double));
    for (int l = 0; l < k; ++l) {
        c[l] = malloc(m * sizeof(double));
        c1[l] = malloc(m * sizeof(double));
    }

    counts = malloc(k * sizeof(int));

#pragma scop
    exec(PAPI_start(set));

    for(i = 0; i < k; i++)
    {
        for(j = 0; j < m; j++)
        {
            c[i][j] =(counts[i]?c1[i][j] / counts[i] : c1[i][j]);
        }
    }

    exec(PAPI_stop(set, values));
#pragma endscop
}