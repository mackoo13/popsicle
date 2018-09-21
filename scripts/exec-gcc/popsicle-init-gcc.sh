#!/bin/bash

# PARAMS: none

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

compile_exec_loop() {
    gcc -c \
        ${root_dir}/papi/exec_loop.c \
        -o ${root_dir}/papi/exec_loop.o
}

compile_papi_utils() {
    gcc -c \
        ${root_dir}/papi/papi_utils.c \
        -o ${root_dir}/papi/papi_utils.o
}

compile_exec_loop
compile_papi_utils
