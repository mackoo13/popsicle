#!/bin/bash

# PARAMS: $1

gcc ${PAPI_UTILS_PATH}/papi_events.c \
    ${PAPI_UTILS_PATH}/papi_utils.o \
    -lpfm \
    -lpapi \
    -static -o ${PAPI_UTILS_PATH}/papi_events

${PAPI_UTILS_PATH}/papi/papi_events $1
