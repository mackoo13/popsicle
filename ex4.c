#include <time.h>
#include "kernels/kernel1.h"
#include "papi_utils/papi_events.h"

int main() {

    int set = PAPI_NULL;
    int event_count;
    create_some_event_set(&set, &event_count);
    printf("%d\n", set);

    long_long* values = malloc(event_count * sizeof(long_long));

    exec(PAPI_start(set));

    clock_t begin = clock();

    loop();

    clock_t end = clock();

    exec(PAPI_stop(set, values));

    print_values(set, values);

    double time_spent = (double)(end - begin) * 1000 / CLOCKS_PER_SEC;
    printf("%lf\n", time_spent);
}