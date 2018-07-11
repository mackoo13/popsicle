#include <stdio.h>
#include <stdlib.h>

extern int max;

int loop() {
    int q=0;
    int* arr = malloc(max * sizeof(int));

    for (int i = 0; i < max; ++i) {
        q += arr[i];
    }
}