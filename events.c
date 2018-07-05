#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

void initialize() {
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);
}

int* available_event_codes(int* res, int* number) {
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

int print_events_list() {
    int retval, is_available;
    int available_count = 0;
    int i = PAPI_PRESET_MASK;
    PAPI_event_info_t info;

    initialize();

    do {
        retval = PAPI_get_event_info(i, &info);

        if (retval == PAPI_OK) {
            is_available = (PAPI_query_event(i) == PAPI_OK);
            if(is_available) available_count++;

            printf("%s\t%-16s %d\t%s\n",
                   (is_available ? "[+]" : "[ ]"),
                   info.symbol,
                   info.event_code % 256,
                   info.long_descr);
        }
    } while (PAPI_enum_event(&i, PAPI_ENUM_ALL) == PAPI_OK);

    printf("\nAvailable events: %d\n", available_count);
}

int main() {
//    print_events_list();

    int res[256];
    char EventCodeStr[PAPI_MAX_STR_LEN];
    int number;
    available_event_codes(res, &number);

    for (int i = 0; i < number; ++i) {
        PAPI_event_code_to_name(res[i], EventCodeStr);
        printf("%s\n", EventCodeStr);
    }
}
