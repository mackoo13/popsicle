#!/bin/bash

readonly trials=5
readonly pb_path=~/polybench-c-4.2.1-beta
readonly papi_path=~/papi/papi/src/

process_file() {
    path=$1
    name=$2

    echo "Processing $name ..."

    # todo add explaining comments

    sed -r 's@int main\(int argc, char\*\* argv\)@int loop\(int set, long_long\* values\)@g;
         s@#include <polybench.h>@#include <polybench.h>\n#include <papi.h>\n#include "../../papi_utils/papi_events.h"@g;
         s@(polybench_prevent_dce[^;]*;)@/*\1*/@g;
         s@(polybench_start_instruments;)@exec\(PAPI_start\(set\)\);@g;
         s@(polybench_stop_instruments;)@exec\(PAPI_stop\(set, values\)\);@g;
         s@(polybench_print_instruments;)@/*\1*/@g' ${path} > kernels_pb/${name}/${name}.c

     python3 param_range.py ${name} > kernels_pb/${name}/${name}_params.txt
}

compile() {
    name=$1

    # todo compile pb

    gcc -c \
        -I ${papi_path} \
        -O0 \
        exec_loop_pb.c
}

compile ${name}

while read -r path; do
    name=`basename "${path%.*}"`
    mkdir -p kernels_pb/${name}
    cp $(echo ${path/%c/h}) kernels_pb/${name}/

    process_file ${path} ${name}

done <<< `find ${pb_path} -iname '*.c' \
    -not -path '*/utilities/*' \
    -not -path '*/fdtd-2d/*' \
    -not -path '*/durbin/*' \
    -not -path '*/Nussinov.orig.c'`

# todo check why durbin, Nussinov.orig and fdtd-2d cause problems
