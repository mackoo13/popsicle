#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi
if [ ! $# -eq 1 ]; then echo "Usage: ./lore_exec_opt.sh <output file name>"; exit 1; fi

readonly trials=1
readonly out_file_O0=${PAPI_OUT_DIR}/speedup/$1_O0.csv
readonly out_file_O3=${PAPI_OUT_DIR}/speedup/$1_O3.csv

executed=0
failed=0

echo -n "alg,run," > ${out_file_O0}
echo -n "alg,run," > ${out_file_O3}
${scripts_dir}/papi/papi_events.sh >> ${out_file_O0}
${scripts_dir}/papi/papi_events.sh >> ${out_file_O3}
echo ",time_O0" >> ${out_file_O0}
echo ",time_O3" >> ${out_file_O3}

echo "Compiling..."
${current_dir}/init.sh

while read -r path; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ${current_dir}/compile_opt.sh ${file_prefix} "${params}" 0; then break; fi
            if ! ${current_dir}/compile_opt.sh ${file_prefix} "${params}" 3; then break; fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop_O0); then
                    echo ${name},${params},${res} >> ${out_file_O0}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi

                if res=$(timeout 10 ${root_dir}/exec_loop_O3); then
                    echo ${name},${params},${res} >> ${out_file_O3}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${LORE_PROC_PATH} -iname '*.c'`

echo ${executed} executed, ${failed} skipped.
