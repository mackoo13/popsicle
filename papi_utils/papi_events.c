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

void create_some_event_set(int* set, int* number) {
    int retval;

    int event_codes[256];
    int event_count;
    available_event_codes(event_codes, &event_count);

    *number = 0;
    PAPI_create_eventset (set);

    for (int i = 0; i < event_count; ++i) {
        retval = PAPI_add_event(*set, event_codes[i]);
        if(retval == PAPI_OK) *number = *number + 1;
    }
}

void print_events_list() {
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

void print_values(int set, long_long* values) {
    int event_codes[256];
    int event_count;
    exec(PAPI_list_events(set, event_codes, &event_count));

//    char event_name[PAPI_MAX_STR_LEN];
    for (int i = 0; i < event_count; ++i) {
//        PAPI_event_code_to_name(event_codes[i], event_name);
//        printf("%s\t%lld\n", event_name, values[i]);
        printf("%lld,", values[i]);

    }
}

void print_event_chooser() {
    // one big todo
    int event_codes[256];
    int event_count;
    int set = PAPI_NULL;
    int retval;

    available_event_codes(event_codes, &event_count);

    for (int i = 0; i < event_count; ++i) {
        for (int j = 0; j < event_count; ++j) {
            if(i == j) {
                printf("-");
                continue;
            }

            PAPI_cleanup_eventset(set);
            PAPI_destroy_eventset(&set);
            PAPI_create_eventset (&set);

            PAPI_add_event(set, event_codes[i]);
            retval = PAPI_add_event(set, event_codes[j]);
            if(retval == PAPI_OK) {
                printf(" ");
            } else {
                printf("X");
            }
        }
        printf("\n");
    }
}