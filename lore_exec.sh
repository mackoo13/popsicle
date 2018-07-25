#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

readonly trials=1
readonly papi_path=~/papi/papi/src/
readonly out_file=../papi_output/$1.csv
readonly kernel_path=../kernels_lore/proc

compile() {
    name=$1
    params=$2

    gcc -c \
        -I ${papi_path} \
        ${kernel_path}/${name}/${name}.c \
        ${params} \
        -O0 -o ${kernel_path}/${name}/${name}.o

    if [ -e ${kernel_path}/${name}/${name}.o ]; then
        gcc ${kernel_path}/${name}/${name}.o \
            exec_loop_pb.o \
            papi_utils/papi_events.o \
            -L ~/papi/papi/src/libpfm4/lib -lpfm \
            -L ~/papi/papi/src/ -lpapi \
            -lm \
            -O0 -static -o exec_loop_pb
     else
        echo "Skipping $name (parse error)"
     fi
}

cat papi_utils/active_events_header.txt > ${out_file}

while read -r path; do
    name=`basename "${path%.*}"`

    while read -r params; do
        compile ${name} "${params}"

        echo "Running $name $params ..."

        for trial in `seq ${trials}`; do
            if res=$(timeout 10 ./exec_loop_pb); then
                echo ${name},${params},${res} >> ${out_file}
#                echo -n ${name},${params},${res}, >> ${out_file}
#                { command time -v ./exec_loop_pb; } 2>&1 | grep "Maximum resident" | grep -oE "[^ ]+$" >> ${out_file}
            else
                echo ":("
                break 2
            fi
        done

    done < ${kernel_path}/${name}/${name}_params.txt

done <<< `find $kernel_path/ -iname '*01*.c'`
