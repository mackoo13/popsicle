#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

file_prefix=$1
params=$2
unroll=$3

clang -c -O3 \
    ${file_prefix}.c \
    ${params} \
    -D PRAGMA_UNROLL='"'${unroll}'"' \
    -o ${file_prefix}_${unroll}.o

if [ -e ${file_prefix}_${unroll}.o ]; then
    clang ${file_prefix}_${unroll}.o \
        ${root_dir}/papi/exec_loop.o \
        ${root_dir}/papi/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${root_dir}/exec_loop_${unroll}
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi