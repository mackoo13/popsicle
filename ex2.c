#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_EVENTS 1

void handle_error (int retval)
{
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

int ex(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}

int main()
{
    int Events[NUM_EVENTS] = {PAPI_TOT_INS};
    long_long values[NUM_EVENTS];
    int retval;


    // Init
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);

    // Event set
    int EventSet = PAPI_NULL;
    ex(PAPI_create_eventset(&EventSet));
//    ex(PAPI_add_event(EventSet, PAPI_L1_DCM));


    // Components
    int num_comp = PAPI_num_components();
    const PAPI_component_info_t *cmpinfo = NULL;

    printf("Components: %d\n", num_comp);
    for (int i = 0; i < num_comp; ++i) {
        cmpinfo = PAPI_get_component_info(i);
        printf("%s\n", cmpinfo->name);
        printf("\tNative events: %d\n", cmpinfo->num_native_events);
        printf("\tPreset Events: %d\n", cmpinfo->num_preset_events);
        printf("\tDisabled: %s\n", cmpinfo->disabled_reason);
    }


    printf("Counters: %d\n", PAPI_num_counters());



/* Start counting events */
    retval = PAPI_start_counters(Events, NUM_EVENTS);
    printf("Start: %d\n", retval);
    if (retval != PAPI_OK)
        handle_error(retval);

/* Read the counters */
    retval = PAPI_read_counters(values, NUM_EVENTS);
    printf("%d\n", retval);
    if (retval != PAPI_OK)
        handle_error(retval);

    printf("After reading the counters: %lld\n",values[0]);

/* Add the counters */
    if (PAPI_accum_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(103);
    printf("After adding the counters: %lld\n", values[0]);

/* Stop counting events */
    if (PAPI_stop_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(104);

    printf("After stopping the counters: %lld\n", values[0]);
}

// gcc -I ~/papi/papi/src/ -c ex2.c
// gcc ex2.o -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2

// gcc ex2.c -I ~/papi/papi/src/ -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2