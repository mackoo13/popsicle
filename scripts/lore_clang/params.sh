#!/bin/bash

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi

parsed=0
failed=0

for path in ${LORE_PROC_PATH}*/; do
    name=`basename "${path%.*}"`

    echo "Generating params for $name"

    if res=`python3 ${root_dir}/lore/lore_params_clang.py ${path}`; then
        ((parsed++))
    else
        ((failed++))
    fi

done

echo ${parsed} parsed, ${failed} skipped.
