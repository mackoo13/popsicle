#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

//#define NUM_FLOPS 10000
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

/* Read the counters */
    if (PAPI_read_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);

    printf("After reading the counters: %lld\n",values[0]);

/* Add the counters */
    if (PAPI_accum_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);
    printf("After adding the counters: %lld\n", values[0]);

/* Stop counting events */
    if (PAPI_stop_counters(values, NUM_EVENTS) != PAPI_OK)
        handle_error(1);

    printf("After stopping the counters: %lld\n", values[0]);
}

// gcc -I ~/papi/papi/src/ -c ex2.c
// gcc ex2.o -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2

// gcc ex2.c -I ~/papi/papi/src/ -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o ex2