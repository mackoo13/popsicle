#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

void handle_error (int retval)
{
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

void initialize() {
    if(!PAPI_is_initialized()) PAPI_library_init(PAPI_VER_CURRENT);
}

void list_components() {
    int num_comp = PAPI_num_components();
    printf("Components count: %d\n", num_comp);

    const PAPI_component_info_t *cmpinfo = NULL;
    for (int i = 0; i < num_comp; ++i) {
        cmpinfo = PAPI_get_component_info(i);
        printf("\t[%d] %s\n", i, cmpinfo->name);
        printf("\t\tNative events: %d\n", cmpinfo->num_native_events);
        printf("\t\tPreset Events: %d\n", cmpinfo->num_preset_events);
        if(cmpinfo->disabled) printf("\t\tWARNING! Component disabled - reason: %s\n", cmpinfo->disabled_reason);
        printf("\n");
    }
}

void list_events() {
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

int exec(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}