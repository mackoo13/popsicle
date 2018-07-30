#include <stdio.h>
#include <papi.h>
#include "papi_utils.h"

int main() {

    int retval;
    int is_first = 1;
    int i = PAPI_PRESET_MASK;
    PAPI_event_info_t info;

    initialize();

    do {
        retval = PAPI_get_event_info(i, &info);

        if (retval == PAPI_OK && PAPI_query_event(i) == PAPI_OK) {
            if(is_first == 0) printf(",");
            is_first = 0;
            printf("%s", info.symbol);
        }
    } while (PAPI_enum_event(&i, PAPI_ENUM_ALL) == PAPI_OK);

    return 0;
}