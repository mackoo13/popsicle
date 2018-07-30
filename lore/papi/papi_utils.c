#include <stdio.h>
#include <stdlib.h>
#include <papi.h>

void handle_error (int retval) {
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

int exec(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}

void initialize() {
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);
}

void available_event_codes(int* res, int* number) {
    int i = PAPI_PRESET_MASK;
    int event_count;
    PAPI_event_info_t info;

    event_count = 0;
    initialize();

    do {
        if ((PAPI_get_event_info(i, &info) == PAPI_OK) && (PAPI_query_event(i) == PAPI_OK)) {
            res[event_count] = info.event_code;
            event_count++;
        }
    } while (PAPI_enum_event(&i, PAPI_ENUM_ALL) == PAPI_OK);

    *number = event_count;
}