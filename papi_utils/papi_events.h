#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

void handle_error(int retval);

void initialize();

void available_event_codes(int* res, int* number);

void print_events_list();

void print_event_chooser();

void exec(int retval);