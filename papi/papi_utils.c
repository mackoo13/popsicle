#include <stdio.h>
#include <stdlib.h>
#include <papi.h>
#include <string.h>

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

void load_event_names(char* file_path, int* res, int* number) {
    FILE* stream = fopen(file_path, "r");
    *number = 0;

    char line[PAPI_MAX_STR_LEN];
    while(fgets(line, PAPI_MAX_STR_LEN, stream)) {
        line[strcspn(line, "\n")] = 0;  // get rid of newline
        exec(PAPI_event_name_to_code(line, &res[*number]));
        *number = *number + 1;
    }
}