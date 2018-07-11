#include <time.h>
#include "kernels/kernel.h"
#include "papi_utils/papi_events.h"

#define TRIALS_COUNT 1  // todo run multiple times

void print_result(int set, long_long* values, double time_spent) {
    int event_codes[256];
    int event_count;
    exec(PAPI_list_events(set, event_codes, &event_count));

    for (int i = 0; i < event_count; ++i) {
        printf("%lld,", values[i]);
    }
    printf("%lf\n", time_spent);
}

int main() {

    int set = PAPI_NULL;
    int event_codes[256];
    int event_count;

    initialize();
    exec(PAPI_multiplex_init());

    available_event_codes(event_codes, &event_count);
    long_long* values = malloc(event_count * sizeof(long_long));

    exec(PAPI_create_eventset(&set));
    exec(PAPI_assign_eventset_component(set, 0));   // todo get cmp
    exec(PAPI_set_multiplex(set));
    exec(PAPI_add_events(set, event_codes, event_count));

    for (int trial = 0; trial < TRIALS_COUNT; ++trial) {
        exec(PAPI_start(set));
        clock_t begin = clock();

        loop();

        clock_t end = clock();
        exec(PAPI_stop(set, values));

        double time_spent = (double)(end - begin) * 1000 / CLOCKS_PER_SEC;
        print_result(set, values, time_spent);
    }


}