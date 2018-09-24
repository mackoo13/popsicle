#!/bin/bash

# PARAMS:
#   $1 input file path

path=$1
dir_path=`dirname ${path}`
file_name=`basename ${path}`
file_name_without_ext=${file_name%.*}

popsicle-init-time.s

echo "Adding PAPI instructions to ${path}"
popsicle-transform-user-input $path

echo "Compiling..."
popsicle-compile-time.sh ${dir_path}/${file_name_without_ext} ""

out_file=${OUT_DIR}/input/${file_name_without_ext}_papi.csv
echo -n "alg,run," > ${out_file}
papi-events.sh >> ${out_file}
echo ",time" >> ${out_file}

echo "Executing ${PAPI_UTILS_PATH}/exec_loop ..."
if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop); then
    echo -n "pred,," >> ${out_file}
    echo ${res} >> ${out_file}
    popsicle-predict -i ${out_file}
else
    echo ":("
fi
