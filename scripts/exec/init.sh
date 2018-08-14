#!/bin/bash

# PARAMS: none

. ../../config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

compile_exec_loop() {
    gcc -c \
        -I ${PAPI_PATH} \
        papi/exec_loop.c \
        -o papi/exec_loop.o
}

compile_papi_utils() {
    gcc -c \
        -I ${PAPI_PATH} \
        papi/papi_utils.c \
        -o papi/papi_utils.o
}

compile_exec_loop
compile_papi_utils
