#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)
#   $2 path to the list of papi events to measure (optional)

if [ -z "$LORE_PROC_CLANG_PATH" ]; then echo "Invalid config (LORE_PROC_CLANG_PATH) missing!"; exit 1; fi
if [ -z "$OUT_DIR" ]; then echo "Invalid config (OUT_DIR) missing!"; exit 1; fi

readonly trials=3
readonly out_file_ur=${OUT_DIR}/unroll/$1_ur.csv
readonly out_file_nour=${OUT_DIR}/unroll/$1_nour.csv
readonly papi_events_list=$2

executed=0
failed=0

echo "Compiling..."
popsicle-init-unroll

echo -n "alg,run," > ${out_file_ur}
echo -n "alg,run," > ${out_file_nour}
papi-events.sh ${papi_events_list} >> ${out_file_ur}
papi-events.sh ${papi_events_list} >> ${out_file_nour}
echo ",time_ur" >> ${out_file_ur}
echo ",time_nour" >> ${out_file_nour}

start_time=$SECONDS

file_count=`find ${LORE_PROC_CLANG_PATH} -iname '*.c' | wc -l`
file_i=1

for path in `find ${LORE_PROC_CLANG_PATH} -iname '*.c'`; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_CLANG_PATH}/${name}/${name}
    ((file_i++))

    # todo else write que pasa
    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ${current_dir}/compile.sh ${file_prefix} "${params}" "unroll(8)"; then break; fi
            if ! ${current_dir}/compile.sh ${file_prefix} "${params}" "nounroll"; then break; fi

            echo "[$file_i/$file_count] Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop_u ${papi_events_list}); then
                    echo ${name},${params},${res} >> ${out_file_ur}
                    ((executed++))
                else
                    echo "Execution error. :("
                    ((failed++))
                    break 2
                fi
            done

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${root_dir}/exec_loop_n ${papi_events_list}); then
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

exec_time=$(($SECONDS - start_time))

echo =========
echo ${executed} executed, ${failed} skipped.
echo "Time: $((exec_time / 3600))h $((exec_time % 3600 / 60))m $((exec_time % 60))s"
