#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)
#   $2 path to the list of papi events to measure (optional)

current_dir=$(dirname $(readlink -f $0))
scripts_dir=${current_dir}/../
root_dir=${scripts_dir}/../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ ! $# -eq 1 ]; then echo "Usage: ./lore_exec_opt.sh <output file name>"; exit 1; fi

readonly trials=1
readonly out_file_O0=${PAPI_OUT_DIR}/speedup/$1_O0.csv
readonly out_file_O3=${PAPI_OUT_DIR}/speedup/$1_O3.csv
readonly papi_events_list=$2

executed=0
failed=0

echo "Compiling..."
${current_dir}/init.sh

echo -n "alg,run," > ${out_file_O0}
echo -n "alg,run," > ${out_file_O3}
${scripts_dir}/papi/papi_events.sh ${papi_events_list} >> ${out_file_O0}
${scripts_dir}/papi/papi_events.sh ${papi_events_list} >> ${out_file_O3}
echo ",time_O0" >> ${out_file_O0}
echo ",time_O3" >> ${out_file_O3}

start_time=$SECONDS

file_count=`find ${LORE_PROC_PATH} -iname '*.c' | wc -l`
file_i=1

for path in `find ${LORE_PROC_PATH} -iname '*.c'`; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ${current_dir}/compile_opt.sh ${file_prefix} "${params}" 0; then break; fi
            if ! ${current_dir}/compile_opt.sh ${file_prefix} "${params}" 3; then break; fi

            echo "[$file_i/$file_count] Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop_O0 ${papi_events_list}); then
                    echo ${name},${params},${res} >> ${out_file_O0}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi

                if res=$(timeout 10 ${root_dir}/exec_loop_O3 ${papi_events_list}); then
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

    ((file_i++))
done

exec_time=$(($SECONDS - start_time))

echo =========
echo ${executed} executed, ${failed} skipped.
echo "Time: $((exec_time / 3600))h $((exec_time % 3600 / 60))m $((exec_time % 60))s"
