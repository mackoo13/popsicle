#!/bin/bash

. lore.cfg

if [ ! -d "$LORE_PROC_PATH" ]; then
    mkdir ${LORE_PROC_PATH}
fi

while read -r path; do
    name=`basename "${path%.*}"`

    echo "Parsing $name"

    if grep -q struct "$path"; then
        echo \t"Skipping $name (struct detected)"
        continue
    fi

    python3 lore_proc.py ${path} ${LORE_PROC_PATH}

done <<< `find ${LORE_ORIG_PATH} -iname '*51_34*.c'`
