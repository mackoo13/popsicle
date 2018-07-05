#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_EVENTS 1

void handle_error (int retval)
{
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

void initialize() {
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);
}

void list_components() {
    int num_comp = PAPI_num_components();
    printf("Components count: %d\n", num_comp);

    const PAPI_component_info_t *cmpinfo = NULL;
    for (int i = 0; i < num_comp; ++i) {
        cmpinfo = PAPI_get_component_info(i);
        printf("\t[%d] %s\n", i, cmpinfo->name);
        printf("\t\tNative events: %d\n", cmpinfo->num_native_events);
        printf("\t\tPreset Events: %d\n", cmpinfo->num_preset_events);
        if(cmpinfo->disabled) printf("\t\tWARNING! Component disabled - reason: %s\n", cmpinfo->disabled_reason);
    }
}

int exec(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}

int main()
{
    int Events[NUM_EVENTS] = {PAPI_TOT_INS};
    long_long values[NUM_EVENTS];
    int retval;

    initialize();
    list_components();

    printf("Counters count: %d\n", PAPI_num_counters());

    // Start counting events
    exec(PAPI_start_counters(Events, NUM_EVENTS));

    // Read the counters
    exec(PAPI_read_counters(values, NUM_EVENTS));
    printf("After reading the counters: %lld\n",values[0]);

    // Add the counters
    exec(PAPI_accum_counters(values, NUM_EVENTS));
    printf("After adding the counters: %lld\n", values[0]);

    // Stop counting events
    exec(PAPI_stop_counters(values, NUM_EVENTS));
    printf("After stopping the counters: %lld\n", values[0]);
}

// gcc -I ~/papi/papi/src/ -c ex2.c
// gcc ex2.o -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2

// gcc ex2.c -I ~/papi/papi/src/ -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2