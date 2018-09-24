#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)
#   $2 path to the list of papi events to measure (optional)

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ ! $# -eq 1 ]; then echo "Usage: popsicle-exec-gcc.sh <output file name>"; exit 1; fi

readonly trials=5
readonly out_file_O0=${OUT_DIR}/gcc/$1_O0.csv
readonly out_file_O3=${OUT_DIR}/gcc/$1_O3.csv
readonly papi_events_list=$2

executed=0
failed=0

echo "Compiling..."
popsicle-init-gcc.sh

echo -n "alg,run," > ${out_file_O0}
echo -n "alg,run," > ${out_file_O3}
papi-events.sh ${papi_events_list} >> ${out_file_O0}
papi-events.sh ${papi_events_list} >> ${out_file_O3}
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
            if ! popsicle-compile-gcc.sh ${file_prefix} "${params}" 0; then break; fi
            if ! popsicle-compile-gcc.sh ${file_prefix} "${params}" 3; then break; fi

            echo "[$file_i/$file_count] Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop_O0 ${papi_events_list}); then
                    echo ${name},${params},${res} >> ${out_file_O0}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi

                if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop_O3 ${papi_events_list}); then
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
