#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_OUT_DIR" ]; then echo "Invalid config (PAPI_OUT_DIR) missing!"; exit 1; fi

readonly trials=1
readonly out_file=${PAPI_OUT_DIR}$1.csv


echo -n "alg,run," > ${out_file}
${root_dir}/papi/papi_events.sh >> ${out_file}
echo ",time" >> ${out_file}

${current_dir}/init.sh

while read -r path; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ${current_dir}/compile.sh ${file_prefix} "${params}"; then
                break
            fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${LORE_PROC_PATH} -iname '*000*.c'`
