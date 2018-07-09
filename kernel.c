#include <stdio.h>

void f() {
    int q=0;

    for (int i = 0; i < 999; ++i) {
        q += i;
    }

    printf("%d\n", q);
}