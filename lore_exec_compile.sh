#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

. config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

readonly trials=1


file_prefix=$1
params=$2

gcc -c \
    -I ${PAPI_PATH} \
    ${file_prefix}.c \
    ${params} \
    -O0 -o ${file_prefix}.o

if [ -e ${file_prefix}.o ]; then
    gcc ${file_prefix}.o \
        papi/exec_loop.o \
        papi/papi_utils.o \
        -L ${PAPI_PATH}libpfm4/lib -lpfm \
        -L ${PAPI_PATH} -lpapi \
        -lm \
        -static -o exec_loop
else
    echo "Skipping $file_prefix (compilation error)"
    return 1
fi
