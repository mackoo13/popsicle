#!/bin/bash

# PARAMS:
#   $1 input file path

path=$1
name=${path%.*}
bkp_path=${path}.bkp

popsicle-init-time.sh

echo "Adding PAPI instructions to ${path}"
popsicle-transform-user-input $1

echo "Compiling..."
popsicle-compile-time.sh ${name} ""

out_file=${name}_papi.csv
papi-events.sh > ${out_file}
echo ",time" >> ${out_file}

echo "Executing ${PAPI_UTILS_PATH}/exec_loop ..."
if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop); then
    echo ${res} >> ${out_file}
    popsicle-predict t -i ${out_file}
else
    echo ":("
fi
