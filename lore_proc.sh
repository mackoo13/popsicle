#!/bin/bash

while read -r path; do
    name=`basename "${path%.*}"`

    if grep -q struct "$path"; then
        echo "Skipping $name (struct detected)"
        continue
    else
        echo "Parsing $name"
    fi

    python3 lore.py ${name}.c

done <<< `find kernels_lore/orig/ -iname '*.c'`
