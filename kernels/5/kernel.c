#include <stdio.h>
#include <stdlib.h>

extern int max;

int loop() {
    int q=0;
    int* arr = malloc(max * sizeof(int));

    for (int i = 0; i < max; ++i) {
        if(i%7==0 || i%3==0) {
            q += arr[i];
        }
    }
}