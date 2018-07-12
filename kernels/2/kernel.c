#include <stdio.h>

extern int max;

int loop() {
    double q=0;

    for (int i = 0; i < max; ++i) {
        q += 54545.99/(i+1);
    }
}