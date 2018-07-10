#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

void handle_error(int retval);

void exec(int retval);

void initialize();

void available_event_codes(int* res, int* number);