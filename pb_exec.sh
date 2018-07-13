#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

readonly trials=5
readonly pb_path=~/polybench-c-4.2.1-beta
readonly papi_path=~/papi/papi/src/
readonly out_file=papi_output/$1.csv
id=0

compile() {
    name=$1

    # todo compile pb

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

    compile ${name}

    echo "Running $name ..."

    for trial in `seq ${trials}`
    do
        echo -n ${id}, >> ${out_file}
        ./exec_loop_pb >> ${out_file}
    done

    ((id++))

done <<< `find kernels_pb -iname '*.c'`
