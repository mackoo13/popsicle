#!/bin/bash

current_dir=$(dirname $(readlink -f $0))
root_dir=${current_dir}/../../
. ${root_dir}/config/lore.cfg

if [ -z "$LORE_ORIG_PATH" ]; then echo "Invalid config (LORE_ORIG_PATH) missing!"; exit 1; fi
if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi

if [ ! -d "$LORE_PROC_PATH" ]; then
    mkdir -p ${LORE_PROC_PATH}
fi

parsed=0
failed=0

for path in `find ${LORE_ORIG_PATH} -iname '*.c'`; do
    name=`basename "${path%.*}"`

    echo "Parsing $name"

    if res=`python3 ${root_dir}/lore/lore_proc_clang.py ${path} ${LORE_PROC_PATH}`; then
        ((parsed++))
        echo $res
    else
        ((failed++))
    fi

done

echo ${parsed} parsed, ${failed} skipped.
