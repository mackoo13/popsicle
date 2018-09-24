#!/bin/bash

# PARAMS: none

compile_exec_loop() {
    clang -c \
        ${PAPI_UTILS_PATH}/exec_loop.c \
        -o ${PAPI_UTILS_PATH}/papi/exec_loop.o
}

compile_papi_utils() {
    clang -c \
        ${PAPI_UTILS_PATH}/papi/papi_utils.c \
        -o ${PAPI_UTILS_PATH}/papi/papi_utils.o
}

compile_exec_loop
compile_papi_utils
