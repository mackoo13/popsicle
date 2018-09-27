#!/bin/bash

# PARAMS:
#   $1 input file path

mode=$1
path=$2
dir_path=`dirname ${path}`
file_name=`basename ${path}`
file_name_without_ext=${file_name%.*}

if [[ ${mode} == "t" || ${mode} == "g" ]]; then
    popsicle-init-time.sh
elif [[ ${mode} == "u" ]]; then
    popsicle-init-unroll.sh
else
    echo "Available modes are: t (time), g (gcc) and u (unroll)."
    exit 1
fi

echo "Adding PAPI instructions to ${path}"
popsicle-transform-user-input ${path}

echo "Compiling..."
if [[ ${mode} == "t" || ${mode} == "g" ]]; then
    popsicle-compile-time.sh ${dir_path}/${file_name_without_ext}_papi ""
elif [[ ${mode} == "u" ]]; then
    popsicle-compile-unroll.sh ${dir_path}/${file_name_without_ext}_papi ""
else
    echo "Available modes are: t (time), g (gcc) and u (unroll)."
    exit 1
fi

mkdir -p ${OUT_DIR}/predict/
out_file=${OUT_DIR}/predict/${file_name_without_ext}_papi.csv

echo -n "alg,run," > ${out_file}
papi-events.sh >> ${out_file}
echo ",time" >> ${out_file}

echo "Executing ${PAPI_UTILS_PATH}/exec_loop ..."
if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop); then
    echo -n "$file_name,," >> ${out_file}
    echo ${res} >> ${out_file}
    popsicle-predict-ml -i ${out_file}
else
    echo ":("
fi
