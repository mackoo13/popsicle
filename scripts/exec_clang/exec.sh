#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_OUT_DIR" ]; then echo "Invalid config (PAPI_OUT_DIR) missing!"; exit 1; fi

readonly trials=1
readonly out_file_ur=${PAPI_OUT_DIR}/unroll/$1_ur.csv
readonly out_file_nour=${PAPI_OUT_DIR}/unroll/$1_nour.csv

executed=0
failed=0

echo -n "alg,run," > ${out_file_ur}
echo -n "alg,run," > ${out_file_nour}
${scripts_dir}/papi/papi_events.sh >> ${out_file_ur}
${scripts_dir}/papi/papi_events.sh >> ${out_file_nour}
echo ",time_O0" >> ${out_file_ur}
echo ",time_O3" >> ${out_file_nour}

${current_dir}/init.sh

for path in `find ${LORE_PROC_PATH} -iname '*.c'`; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ${current_dir}/compile.sh ${file_prefix} "${params}" "unroll"; then break; fi
            if ! ${current_dir}/compile.sh ${file_prefix} "${params}" "nounroll"; then break; fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop); then
                    echo ${name},${params},${res} >> ${out_file_ur}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi
            done

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop); then
                    echo ${name},${params},${res} >> ${out_file_nour}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done
