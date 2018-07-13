#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

name=2mm
readonly pb_path=~/polybench-c-4.2.1-beta
readonly papi_path=~/papi/papi/src/
readonly out_file=papi_output/$1.csv

process_file() {
    path=$1
    name=$2

    echo "Processing $name ..."

    sed -r 's@int main\(int argc, char\*\* argv\)@int loop\(int set, long_long\* values\)@g;
         s@#include <polybench.h>@#include <polybench.h>\n#include <papi.h>\n#include "../../papi_utils/papi_events.h"@g;
         s@(polybench_prevent_dce[^;]*;)@/*\1*/@g;
         s@(polybench_start_instruments;)@exec\(PAPI_start\(set\)\);@g;
         s@(polybench_stop_instruments;)@exec\(PAPI_stop\(set, values\)\);@g;
         s@(polybench_print_instruments;)@/*\1*/@g' ${path} > kernels_pb/${name}/${name}.c
}

compile() {
    name=$1

    # todo compile pb

    gcc -c \
        -I ${papi_path} \
        -I ${pb_path}/utilities/ \
        kernels_pb/${name}/${name}.c \
        -D MEDIUM_DATASET \
        -o kernels_pb/${name}/${name}.o

    gcc -c \
        -I ${papi_path} \
        exec_loop_pb.c

    gcc kernels_pb/${name}/${name}.o \
        exec_loop_pb.o \
        papi_utils/papi_events.o \
        ${pb_path}/utilities/polybench.o  \
        -L ~/papi/papi/src/libpfm4/lib -lpfm \
        -L ~/papi/papi/src/ -lpapi \
        -lm \
        -static -o exec_loop_pb
}

echo -n "" > ${out_file}

while read -r path; do
    name=`basename "${path%.*}"`
    mkdir -p kernels_pb/${name}
    cp $(echo ${path/%c/h}) kernels_pb/${name}/

    # todo add explaining comments

    process_file ${path} ${name}
    compile ${name}

    ./exec_loop_pb >> ${out_file}

done <<< `find ${pb_path} -iname '*.c' \
    -not -path '*/utilities/*' \
    -not -path '*/fdtd-2d/*' \
    -not -path '*/Nussinov.orig.c'`

