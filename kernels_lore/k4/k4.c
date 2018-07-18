// https://vectorization.computer/loop.html?id=32cac7af-ccd2-409d-b02e-0b2c84c2a716&benchmark=cortexsuite&version=default&application=clustering-spectral&file=spectral.c&func=main&line=157

#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
int i;
int n;
int j;
double * A;
double * D;

int loop(int set, long_long* values)
{
#pragma scop

    for(i = 0; i < n; i++)
    {
        for(j = 0; j < n; j++) A[n * i + j] = A[n * i + j] / sqrt(D[i]) / sqrt(D[j]);
    }

#pragma endscop
}
