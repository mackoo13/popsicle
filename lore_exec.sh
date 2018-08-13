#!/bin/bash

# PARAMS:
#   $1 output file name (without extension)

. config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_PATH" ]; then echo "Invalid config (PAPI_PATH) missing!"; exit 1; fi
if [ -z "$PAPI_OUT_DIR" ]; then echo "Invalid config (PAPI_OUT_DIR) missing!"; exit 1; fi

readonly trials=1
readonly out_file=${PAPI_OUT_DIR}$1.csv


echo -n "alg,run," > ${out_file}
./lore_papi_events.sh >> ${out_file}
echo ",time" >> ${out_file}

./lore_exec_init.sh

while read -r path; do
    name=`basename "${path%.*}"`

    file_prefix=${LORE_PROC_PATH}/${name}/${name}

    if [ -e ${file_prefix}_params.txt ]; then
        while read -r params; do
            if ! ./lore_exec_compile.sh ${file_prefix} "${params}"; then
                break
            fi

            echo "Running $name $params ..."

            for trial in `seq ${trials}`; do
                if res=$(timeout 10 ./exec_loop); then
                    echo ${name},${params},${res} >> ${out_file}
                else
                    echo ":("
                    break 2
                fi
            done

        done < ${file_prefix}_params.txt
    fi

done <<< `find ${LORE_PROC_PATH} -iname '*000*.c'`
