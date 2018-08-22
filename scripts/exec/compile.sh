#!/bin/bash

# PARAMS:
#   $1 input file path (without extension)
#   $2 compilation params (e.g. -D N=42), optional

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

readonly trials=1

file_prefix=$1
params=$2

gcc -c \
    ${file_prefix}.c \
    ${params} \
    -O0 -o ${file_prefix}.o

if [ -e ${file_prefix}.o ]; then
    gcc ${file_prefix}.o \
        ${root_dir}/papi/exec_loop.o \
        ${root_dir}/papi/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${root_dir}/exec_loop
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi
