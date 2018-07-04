#include <papi.h>
#include <testlib/do_loops.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_FLOPS 10000
#define NUM_EVENTS 1

void handle_error (int retval)
{
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

int main()
{
    int Events[NUM_EVENTS] = {PAPI_TOT_INS};
    long_long values[NUM_EVENTS];

/* Start counting events */
    if (PAPI_start_counters(Events, NUM_EVENTS) != PAPI_OK)
        handle_error(1);

/* Defined in tests/do_loops.c in the PAPI source distribution */
    do_flops(NUM_FLOPS);

/* Read the counters */
    if (PAPI_read_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);

    printf("After reading the counters: %lld\n",values[0]);

    do_flops(NUM_FLOPS);

/* Add the counters */
    if (PAPI_accum_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);
    printf("After adding the counters: %lld\n", values[0]);

    do_flops(NUM_FLOPS);

/* Stop counting events */
    if (PAPI_stop_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);

    printf("After stopping the counters: %lld\n", values[0]);
}

// gcc -I ~/papi/papi/src ex2.c ~/papi/papi/src/testlib/do_loops.c -L ~/papi/papi/src -lpapi