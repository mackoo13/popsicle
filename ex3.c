#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_EVENTS 2
#define NUM_ITER 999999

void handle_error (int retval)
{
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

void initialize() {
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);
}

void list_values(long long int* values, char* label) {
    printf("%s", label);
    for(int i=0; i<NUM_EVENTS; ++i) {
        printf("\t%lld", values[i]);
    }
    printf("\n");
}

int exec(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}

int main()
{
    int Events[NUM_EVENTS] = {PAPI_TOT_INS, PAPI_L1_DCM};
    long_long values[NUM_EVENTS];
    int retval;
    
    initialize();

    int a[NUM_ITER], b[NUM_ITER];

    exec(PAPI_start_counters(Events, NUM_EVENTS));
    for (int i = 0; i < NUM_ITER; ++i) {
        a[i] = b[i];
    }
    exec(PAPI_stop_counters(values, NUM_EVENTS));
    list_values(values, "After stop");

    exec(PAPI_start_counters(Events, NUM_EVENTS));
    for (int i = 0; i < NUM_ITER; ++i) {
        a[rand()%NUM_ITER] = b[rand()%NUM_ITER];
    }
    exec(PAPI_stop_counters(values, NUM_EVENTS));
    list_values(values, "After stop");}
