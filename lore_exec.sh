#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

# todo slashes in paths

. lore.cfg

if [ -z "$LORE_ORIG_PATH" ]; then echo "Invalid config (LORE_ORIG_PATH) missing!"; exit 1; fi
if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_UTILS_PATH" ]; then echo "Invalid config (PAPI_UTILS_PATH) missing!"; exit 1; fi

readonly trials=1
readonly out_file=${PAPI_OUT_DIR}$1.csv

compile_exec_loop() {
    gcc -c \
        -I ${PAPI_PATH} \
        exec_loop_lore.c \
        -o exec_loop_lore.o
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
            exec_loop_lore.o \
            ${PAPI_UTILS_PATH}papi_events.o \
            -L ${PAPI_PATH}libpfm4/lib -lpfm \
            -L ${PAPI_PATH} -lpapi \
            -lm \
            -O0 -static -o exec_loop_lore
    else
        echo "Skipping $name (compilation error)"
        return 1
    fi
}

cat ${PAPI_UTILS_PATH}active_events_header.txt > ${out_file}

compile_exec_loop

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
                if res=$(timeout 10 ./exec_loop_lore); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${LORE_PROC_PATH} -iname '*.c'`
