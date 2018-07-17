#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

readonly trials=1
readonly pb_path=~/polybench-c-4.2.1-beta
readonly papi_path=~/papi/papi/src/
readonly out_file=papi_output/$1.csv

compile() {
    name=$1
    params=$2

    # todo compile pb

    gcc -c \
        -I ${papi_path} \
        -I ${pb_path}/utilities/ \
        kernels_pb/${name}/${name}.c \
        -D MINI_DATASET \
        ${params} \
        -O0 -o kernels_pb/${name}/${name}.o

    gcc kernels_pb/${name}/${name}.o \
        exec_loop_pb.o \
        papi_utils/papi_events.o \
        ${pb_path}/utilities/polybench.o  \
        -L ~/papi/papi/src/libpfm4/lib -lpfm \
        -L ~/papi/papi/src/ -lpapi \
        -lm \
        -O0 -static -o exec_loop_pb
}

cat papi_utils/active_events_header.txt > ${out_file}

while read -r path; do
    name=`basename "${path%.*}"`

    while read -r params; do
        compile ${name} "${params}"

        echo "Running $name $params ..."

        for trial in `seq ${trials}`; do
            echo -n ${name},${params}, >> ${out_file}
            ./exec_loop_pb >> ${out_file}
        done

    done < kernels_pb/${name}/${name}_params.txt

done <<< `find kernels_pb -iname '*.c'`
