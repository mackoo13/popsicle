#include <stdio.h>
#include <stdlib.h>
int N;
int* A;

void loop()
{

    N = 42;
    A = malloc(N * sizeof(int));

#pragma scop

    for(int i = 0; i < N; i++)
        A[i] += i;

#pragma endscop
}