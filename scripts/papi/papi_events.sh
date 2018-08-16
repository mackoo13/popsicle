#!/bin/bash

# PARAMS: none

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

gcc -c \
    -I ${PAPI_PATH} \
    ${root_dir}/papi/papi_events.c \
    -o ${root_dir}/papi/papi_events.o

if [ -e ${root_dir}/papi/papi_events.o ]; then
    gcc ${root_dir}/papi/papi_events.o \
        ${root_dir}/papi/papi_utils.o \
        -L ${PAPI_PATH}libpfm4/lib -lpfm \
        -L ${PAPI_PATH} -lpapi \
        -static -o ${root_dir}/papi/papi_events
fi

${scripts_dir}/../papi/papi_events
