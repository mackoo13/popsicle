#!/bin/bash

# PARAMS: none

compile_exec_loop() {
    gcc -c \
        ${PAPI_UTILS_PATH}/exec_loop.c \
        -o ${PAPI_UTILS_PATH}/exec_loop.o
}

compile_papi_utils() {
    gcc -c \
        ${PAPI_UTILS_PATH}/papi_utils.c \
        -o ${PAPI_UTILS_PATH}/papi_utils.o
}

compile_exec_loop
compile_papi_utils
