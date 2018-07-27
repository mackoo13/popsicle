#!/bin/bash

. lore.cfg

if [ -z "$LORE_ORIG_PATH" ]; then echo "Invalid config (LORE_ORIG_PATH) missing!"; exit 1; fi
if [ -z "$LORE_PROC_PATH" ]; then echo "Invalid config (LORE_PROC_PATH) missing!"; exit 1; fi

if [ ! -d "$LORE_PROC_PATH" ]; then
    mkdir ${LORE_PROC_PATH}
fi

parsed=0
failed=0

while read -r path; do
    name=`basename "${path%.*}"`

    echo "Parsing $name"

    if grep -q struct "$path"; then
        echo -e "\tSkipping $name (struct detected)"
        continue
    fi

    if res=`python3 lore_proc.py ${path} ${LORE_PROC_PATH}`; then
        ((parsed++))
    else
        ((failed++))
    fi

done <<< `find ${LORE_ORIG_PATH} -iname '*51_34*.c'`

echo ${parsed} parsed, ${failed} skipped.
