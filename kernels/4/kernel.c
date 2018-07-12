#include <stdio.h>
#include <stdlib.h>

extern int max;

int loop() {
    int q=0;
    int* arr = malloc(max * max * sizeof(int));

    for (int i = 1; i < max-1; ++i) {
        for (int j = 1; j < max-1; ++j) {
            q +=
                    arr[(i-1)*max+(j-1)] + arr[(i-1)*max+j] + arr[(i-1)*max+(j+1)] +
                    arr[i*max+(j-1)] + arr[i*max+j] + arr[i*max+(j+1)] +
                    arr[(i+1)*max+(j-1)] + arr[(i+1)*max+j] + arr[(i+1)*max+(j+1)];
        }
    }
}