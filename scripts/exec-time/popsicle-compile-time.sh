#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

readonly trials=1

file_prefix=$1
params=$2

gcc -c \
    ${file_prefix}.c \
    ${params} \
    -O0 -o ${file_prefix}.o

if [ -e ${file_prefix}.o ]; then
    gcc ${file_prefix}.o \
        ${PAPI_UTILS_PATH}/exec_loop.o \
        ${PAPI_UTILS_PATH}/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${PAPI_UTILS_PATH}/exec_loop
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi
