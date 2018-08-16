#!/bin/bash

# PARAMS: none

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

compile_exec_loop() {
    clang -c \
        -I ${PAPI_PATH} \
        ${root_dir}/papi/exec_loop.c \
        -o ${root_dir}/papi/exec_loop.o
}

compile_papi_utils() {
    clang -c \
        -I ${PAPI_PATH} \
        ${root_dir}/papi/papi_utils.c \
        -o ${root_dir}/papi/papi_utils.o
}

compile_exec_loop
compile_papi_utils
