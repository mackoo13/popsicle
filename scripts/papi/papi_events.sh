#!/bin/bash

# PARAMS: none

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

gcc -c \
    ${root_dir}/papi/papi_events.c \
    -o ${root_dir}/papi/papi_events.o

if [ -e ${root_dir}/papi/papi_events.o ]; then
    gcc ${root_dir}/papi/papi_events.o \
        ${root_dir}/papi/papi_utils.o \
        -lpfm \
        -lpapi \
        -static -o ${root_dir}/papi/papi_events
fi

${scripts_dir}/../papi/papi_events
