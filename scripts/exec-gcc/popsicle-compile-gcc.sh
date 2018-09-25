#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

file_prefix=$1
params=$2
optimization=${3:O0}

gcc -c \
    ${file_prefix}.c \
    ${params} \
    -O${optimization} \
    -o ${file_prefix}_O${optimization}.o

if ! [ -e ${PAPI_UTILS_PATH}/exec_loop.o ]; then
    gcc -c ${PAPI_UTILS_PATH}/exec_loop.c
fi

if [ -e ${file_prefix}_O${optimization}.o ]; then
    gcc ${file_prefix}_O${optimization}.o \
        ${PAPI_UTILS_PATH}/exec_loop.o \
        ${PAPI_UTILS_PATH}/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${PAPI_UTILS_PATH}/exec_loop_O${optimization}
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi