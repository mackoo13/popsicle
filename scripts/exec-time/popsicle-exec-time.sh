#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$OUT_DIR" ]; then echo "Invalid config (OUT_DIR) missing!"; exit 1; fi

readonly trials=5
readonly out_file=${OUT_DIR}time/$1.csv

mkdir -p ${OUT_DIR}/time

popsicle-init-time.sh

echo -n "alg,run," > ${out_file}
papi-events.sh >> ${out_file}
echo ",time" >> ${out_file}

for path in `find ${LORE_PROC_PATH} -iname '*.c'`; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! popsicle-compile-time.sh ${file_prefix} "${params}"; then
                break
            fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ${PAPI_UTILS_PATH}/exec_loop); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done
