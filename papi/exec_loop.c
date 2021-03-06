#include <stdio.h>
#include <stdlib.h>
#include "exec_loop.h"
#include "papi_utils.h"

void print_result(int set, long_long* values, double time_spent) {
    int event_codes[256];
    int event_count;
    exec(PAPI_list_events(set, event_codes, &event_count));

    for (int i = 0; i < event_count; ++i) {
        printf("%lld,", values[i]);
    }
    printf("%lf\n", time_spent);
}


int main(int argc, char* argv []) {

    int set = PAPI_NULL;
    int event_codes[256];
    int event_count;
    int retval = 0;

    initialize();
    exec(PAPI_multiplex_init());

    if(argc >= 2) {
        retval = load_event_names(argv[1], event_codes, &event_count);
        if(retval != 0) {
            printf("Cannot open %s (error %d). \n", argv[1], retval);
            return retval;
        }
    } else {
        available_event_codes(event_codes, &event_count);
    }

    long_long* values = malloc(event_count * sizeof(long_long));

    exec(PAPI_create_eventset(&set));
    exec(PAPI_assign_eventset_component(set, 0));
    exec(PAPI_set_multiplex(set));
    exec(PAPI_add_events(set, event_codes, event_count));

    clock_t begin, end;

    loop(set, values, &begin, &end);

    double time_spent = (double)(end - begin) * 1000 / CLOCKS_PER_SEC;
    print_result(set, values, time_spent);
}