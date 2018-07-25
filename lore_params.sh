#!/bin/bash

while read -r path; do
    name=`basename "${path%.*}"`

    echo "Generating params for $name"

    python3 lore_params.py ${name}

done <<< `find ../kernels_lore/proc/ -iname '*01*.c'`
