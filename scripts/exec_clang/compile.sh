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
        ${root_dir}/papi/exec_loop.o \
        ${root_dir}/papi/papi_utils.o \
        -lpfm \
        -lpapi \
        -lm \
        -static -o ${root_dir}/exec_loop_${u_or_n}
else
    echo "Skipping $file_prefix (compilation error)"
    exit 1
fi