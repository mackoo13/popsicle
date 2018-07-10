#include <stdio.h>

int loop() {
    int q=0;

    for (int i = 0; i < 999; ++i) {
        q += i;
    }

    printf("%d\n", q);
}