#include <stdio.h>

extern int max;

int loop() {
    int q=0;

    for (int i = 0; i < max; ++i) {
        q += i;
    }
}