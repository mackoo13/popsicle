#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

. config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

readonly trials=1
readonly out_file=${PAPI_OUT_DIR}$1.csv

csv_header() {
    gcc -c \
        -I ${PAPI_PATH} \
        papi/papi_events.c \
        -o papi/papi_events.o

    if [ -e papi/papi_events.o ]; then
        gcc papi/papi_events.o \
            papi/papi_utils.o \
            -L ${PAPI_PATH}libpfm4/lib -lpfm \
            -L ${PAPI_PATH} -lpapi \
            -static -o papi/papi_events
    fi

    ./papi/papi_events
}

compile_exec_loop() {
    gcc -c \
        -I ${PAPI_PATH} \
        papi/exec_loop.c \
        -o papi/exec_loop.o
}

compile_papi_utils() {
    gcc -c \
        -I ${PAPI_PATH} \
        papi/papi_utils.c \
        -o papi/papi_utils.o
}

compile() {
    file_prefix=$1
    params=$2

    gcc -c \
        -I ${PAPI_PATH} \
        ${file_prefix}.c \
        ${params} \
        -O0 -o ${file_prefix}.o

    if [ -e ${file_prefix}.o ]; then
        gcc ${file_prefix}.o \
            papi/exec_loop.o \
            papi/papi_utils.o \
            -L ${PAPI_PATH}libpfm4/lib -lpfm \
            -L ${PAPI_PATH} -lpapi \
            -lm \
            -O0 -static -o exec_loop
    else
        echo "Skipping $name (compilation error)"
        return 1
    fi
}

csv_header > ${out_file}
compile_exec_loop
compile_papi_utils

while read -r path; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! compile ${file_prefix} "${params}"; then
                break
            fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ./exec_loop); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${LORE_PROC_PATH} -iname '*.c'`
