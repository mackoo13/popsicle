#!/bin/bash

# PARAMS:
#   $1 input file path

. config/lore.cfg

if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi

path=$1
name=${path%.*}
bkp_path=${path}.bkp

./lore_exec_init.sh

echo "Creating a copy of the original file: ${bkp_path}"
if [ -e ${bkp_path} ]; then
    cp ${bkp_path} ${path}
else
    cp ${path} ${bkp_path}
fi

echo "Adding PAPI instructions to ${path}"
python3 lore/lore_add_papi.py $1

echo "Compiling..."
./lore_exec_compile.sh ${name} ""

out_file=${name}_papi.csv
./lore_papi_events.sh > ${out_file}
echo ",time" >> ${out_file}

echo "Executing..."
if res=$(timeout 10 ./exec_loop); then
    echo ${res} >> ${out_file}
    python3 lore/lore_predict_opt.py -i ${out_file}
else
    echo "Runtime error."
fi
