#!/bin/bash

# PARAMS: $1

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

gcc ${root_dir}/papi/papi_events.c \
    ${root_dir}/papi/papi_utils.o \
    -lpfm \
    -lpapi \
    -static -o ${root_dir}/papi/papi_events

${root_dir}/papi/papi_events $1
