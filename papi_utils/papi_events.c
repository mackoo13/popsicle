#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

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
    PAPI_event_info_t info;

    *number = 0;
    initialize();

    do {
        if ((PAPI_get_event_info(i, &info) == PAPI_OK) && (PAPI_query_event(i) == PAPI_OK)) {
            res[*number] = info.event_code;
            *number = *number + 1;
        }
    } while (PAPI_enum_event(&i, PAPI_ENUM_ALL) == PAPI_OK);
}
