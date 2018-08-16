#!/bin/bash

# PARAMS:
#   $1 input file path

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

path=$1
name=${path%.*}
bkp_path=${path}.bkp

${scripts_dir}/exec/init.sh

echo "Creating a copy of the original file: ${bkp_path}"
if [ -e ${bkp_path} ]; then
    cp ${bkp_path} ${path}
else
    cp ${path} ${bkp_path}
fi

echo "Adding PAPI instructions to ${path}"
python3 ${root_dir}/lore/lore_add_papi.py $1

echo "Compiling..."
${scripts_dir}/exec/compile.sh ${name} ""

out_file=${name}_papi.csv
${scripts_dir}/papi/papi_events.sh > ${out_file}
echo ",time" >> ${out_file}

echo "Executing..."
if res=$(timeout 10 ${root_dir}/exec_loop); then
    echo ${res} >> ${out_file}
    python3 ${root_dir}/lore/lore_predict.py -i ${out_file}
else
    echo ":("
fi
