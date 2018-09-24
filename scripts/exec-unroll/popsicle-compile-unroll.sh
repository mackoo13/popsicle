#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

file_prefix=$1
params=$2
unroll=$3
u_or_n=${unroll::1}
vect=""
if [[ ${u_or_n} == "n" ]]; then vect=-fno-vectorize; fi

# Rpass=unroll - shows what unrolling has been performed

# at least O2 to unroll
clang -c -Rpass=unroll -O2 \
    ${file_prefix}.c \
    ${params} \
    ${vect} \
    -D PRAGMA_UNROLL='"'${unroll}'"' \
    -o ${file_prefix}_${u_or_n}.o

if [ -e ${file_prefix}_${u_or_n}.o ]; then
    clang ${file_prefix}_${u_or_n}.o \
        ${PAPI_UTILS_PATH}/exec_loop.o \
        ${PAPI_UTILS_PATH}/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${PAPI_UTILS_PATH}/exec_loop_${u_or_n}
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi