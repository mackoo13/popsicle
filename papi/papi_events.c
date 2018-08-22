#include <stdio.h>
#include <papi.h>
#include <string.h>
#include "papi_utils.h"

int main(int argc, char* argv []) {

    int is_first = 1;

    if(argc > 1) {
        FILE* stream = fopen(argv[1], "r");

        char line[PAPI_MAX_STR_LEN];
        while(fgets(line, PAPI_MAX_STR_LEN, stream)) {
            line[strcspn(line, "\n")] = 0;  // get rid of newline
            if (is_first == 0) printf(",");
            is_first = 0;
            printf("%s", line);
        }
    } else {
        int retval;
        int i = PAPI_PRESET_MASK;
        PAPI_event_info_t info;

        initialize();

        do {
            retval = PAPI_get_event_info(i, &info);

            if (retval == PAPI_OK && PAPI_query_event(i) == PAPI_OK) {
                if (is_first == 0) printf(",");
                is_first = 0;
                printf("%s", info.symbol);
            }
        } while (PAPI_enum_event(&i, PAPI_ENUM_ALL) == PAPI_OK);
    }

    return 0;
}