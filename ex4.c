#include "kernel.h"
#include "papi_utils/papi_events.h"

int main() {

    int set = PAPI_NULL;
    int event_count;
    create_some_event_set(&set, &event_count);

    long_long* values = malloc(event_count * sizeof(long_long));

    initialize();

    exec(PAPI_start(set));

    loop();

    exec(PAPI_stop(set, values));

    print_values(set, values);
}