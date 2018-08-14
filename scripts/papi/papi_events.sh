#!/bin/bash

# PARAMS: none

. ../../config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

gcc -c \
    -I ${PAPI_PATH} \
    ../../papi/papi_events.c \
    -o ../../papi/papi_events.o

if [ -e ../../papi/papi_events.o ]; then
    gcc ../../papi/papi_events.o \
        ../../papi/papi_utils.o \
        -L ${PAPI_PATH}libpfm4/lib -lpfm \
        -L ${PAPI_PATH} -lpapi \
        -static -o ../../papi/papi_events
fi

../../papi/papi_events
