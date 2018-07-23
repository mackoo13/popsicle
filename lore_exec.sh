#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

readonly trials=3
readonly papi_path=~/papi/papi/src/
readonly out_file=papi_output/$1.csv

compile() {
    name=$1
    params=$2

    gcc -c \
        -I ${papi_path} \
        kernels_lore/proc/${name}/${name}.c \
        ${params} \
        -O0 -o kernels_lore/proc/${name}/${name}.o

    if [ -e kernels_lore/proc/${name}/${name}.o ]; then
        gcc kernels_lore/proc/${name}/${name}.o \
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
            if res=$(./exec_loop_pb); then
                echo ${name},${params},${res} >> ${out_file}
            else
                echo ":("
            fi
        done

    done < kernels_lore/proc/${name}/${name}_params.txt

done <<< `find kernels_lore/proc/ -iname '*9c5c*.c'`
