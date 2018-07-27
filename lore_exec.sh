#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

readonly trials=1
readonly papi_path=~/papi/papi/src/
readonly out_file=../papi_output/$1.csv
readonly kernel_path=../kernels_lore/proc

compile_exec_loop() {
    gcc -c \
        -I ${papi_path} \
        exec_loop_lore.c \
        -o exec_loop_lore.o
}

compile() {
    file_prefix=$1
    params=$2

    gcc -c \
        -I ${papi_path} \
        ${file_prefix}.c \
        ${params} \
        -O0 -o ${file_prefix}.o

    if [ -e ${file_prefix}.o ]; then
        gcc ${file_prefix}.o \
            exec_loop_lore.o \
            papi_utils/papi_events.o \
            -L ~/papi/papi/src/libpfm4/lib -lpfm \
            -L ~/papi/papi/src/ -lpapi \
            -lm \
            -O0 -static -o exec_loop_lore
    else
        echo "Skipping $name (compilation error)"
        return 1
    fi
}

cat papi_utils/active_events_header.txt > ${out_file}

compile_exec_loop

while read -r path; do
    name=`basename "${path%.*}"`

    file_prefix=${kernel_path}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! compile ${file_prefix} "${params}"; then
                break
            fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ./exec_loop_lore); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${kernel_path}/ -iname '*.c'`
