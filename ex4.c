#include <time.h>
#include "kernels/kernel.h"
#include "papi_utils/papi_events.h"

#define EVENT_COUNT 4

int main() {

    int set = PAPI_NULL;
    int event_codes[4] = {PAPI_L1_DCM, PAPI_L1_ICM, PAPI_TOT_INS, PAPI_REF_CYC};
    long_long values[EVENT_COUNT];

    initialize();

    exec(PAPI_create_eventset(&set));
    exec(PAPI_add_events(set, event_codes, EVENT_COUNT));

    exec(PAPI_start(set));
    clock_t begin = clock();

    loop();

    clock_t end = clock();
    exec(PAPI_stop(set, values));

    print_values(set, values);

    double time_spent = (double)(end - begin) * 1000 / CLOCKS_PER_SEC;
    printf("%lf\n", time_spent);
}