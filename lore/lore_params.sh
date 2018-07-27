#!/bin/bash

. lore.cfg

while read -r path; do
    echo $path
    name=`basename "${path%.*}"`

    echo "Generating params for $name"

    python3 lore_params.py ${path}

done <<< `ls -d ${LORE_PROC_PATH}*/`
