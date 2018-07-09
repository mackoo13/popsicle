#include "kernel.h"
#include "papi_utils/papi_events.h"

int main() {
    print_event_chooser();

//    int event_codes[256];
    int event_codes[2] = {PAPI_TOT_INS, PAPI_L1_DCM};
    int event_count=2;
//    available_event_codes(event_codes, &event_count);

    char EventCodeStr[PAPI_MAX_STR_LEN];
    for (int i = 0; i < event_count; ++i) {
        PAPI_event_code_to_name(event_codes[i], EventCodeStr);
        printf("%s\n", EventCodeStr);
    }

    long_long* values = malloc(event_count * sizeof(long_long));

    initialize();

    exec(PAPI_start_counters(event_codes, event_count));

//    loop();

    exec(PAPI_stop_counters(values, event_count));
    printf("%d\n", event_count);
    printf("%lld\n", values[0]);
}