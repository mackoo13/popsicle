#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$PIPS_PROC_PATH" ]; then echo "Invalid config (PIPS_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_OUT_DIR" ]; then echo "Invalid config (PAPI_OUT_DIR) missing!"; exit 1; fi

readonly trials=1
readonly out_file=${PAPI_OUT_DIR}$1.csv

${current_dir}/init.sh

echo -n "alg,run," > ${out_file}
${scripts_dir}/papi/papi_events.sh >> ${out_file}
echo ",time" >> ${out_file}

for path in `find ${PIPS_PROC_PATH} -iname '*14_wombat.c'`; do
    file_prefix=${path: 0:-2}

    if ! ${current_dir}/compile.sh ${file_prefix}; then
        break
    fi

    echo "Running $file_prefix ..."

    for trial in `seq ${trials}`; do
        if res=$(timeout 10 ${root_dir}/exec_loop); then
            echo ${file_prefix},,${res} >> ${out_file}
        else
            echo ":("
            break 2
        fi
    done
done
