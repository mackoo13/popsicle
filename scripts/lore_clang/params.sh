#!/bin/bash

. ../../config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi

parsed=0
failed=0

while read -r path; do
    name=`basename "${path%.*}"`

    echo "Generating params for $name"

    if res=`python3 lore/lore_params.py ${path}`; then
        ((parsed++))
    else
        ((failed++))
    fi

done <<< `ls -d ${LORE_PROC_PATH}*/`

echo ${parsed} parsed, ${failed} skipped.
