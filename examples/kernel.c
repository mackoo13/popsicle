#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int N;
int* A;

void loop()
{

    N = 42999999;
    A = malloc((N/1000) * sizeof(int));

#pragma scop

    for(int i = 0; i < N; i++)
        A[i/1000] += i/(i+9999);

#pragma endscop
}