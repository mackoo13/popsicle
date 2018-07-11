#include <time.h>
#include "kernels/kernel.h"
#include "papi_utils/papi_events.h"

int main() {

    int set = PAPI_NULL;
    int event_codes[256] = {PAPI_L1_DCM, PAPI_L1_ICM, PAPI_TOT_INS, PAPI_REF_CYC};
    int event_count;

    available_event_codes(event_codes, &event_count);

    initialize();
    exec(PAPI_create_eventset(&set));

    int res = 0;

    for (int a = 0; a < event_count; ++a) {
        if(PAPI_add_event(set, event_codes[a]) == PAPI_OK) {

            for (int b = a+1; b < event_count; ++b) {
                if(PAPI_add_event(set, event_codes[b]) == PAPI_OK) {

                    for (int c = b+1; c < event_count; ++c) {
                        if(PAPI_add_event(set, event_codes[c]) == PAPI_OK) {

                            for (int d = c+1; d < event_count; ++d) {
                                if(PAPI_add_event(set, event_codes[d]) == PAPI_OK) {
//                                    if(event_codes[a]%256+256!=50&&event_codes[c]%256+256!=50&&event_codes[b]%256+256!=50&&event_codes[d]%256+256!=50)
                                    printf("%d\t%d\t%d\t%d\n",
                                           (event_codes[a]%256+256)%256,
                                           event_codes[b]%256+256,
                                           event_codes[c]%256+256,
                                           event_codes[d]%256+256);
                                    PAPI_remove_event(set, event_codes[d]);
                                    res++;
                                }
                            }
                            PAPI_remove_event(set, event_codes[c]);

                        }
                    }
                    PAPI_remove_event(set, event_codes[b]);

                }
            }
            PAPI_remove_event(set, event_codes[a]);

        }
    }
    printf("%d\n", res);

}