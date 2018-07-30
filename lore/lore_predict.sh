#!/bin/bash

# PARAMS:
#   $1 input file path

. config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi


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

    gcc -c \
        -I ${PAPI_PATH} \
        ${file_prefix}.c \
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

compile_exec_loop
compile_papi_utils

path=$1
name=${path%.*}
compile ${name}

out_file=$name.csv
csv_header > ${out_file}
echo -e \n >> ${out_file}

if res=$(timeout 10 ./exec_loop); then
    echo ${res} >> ${out_file}
    python3 lore/lore_predict.py -i ${out_file}
else
    echo ":("
fi
