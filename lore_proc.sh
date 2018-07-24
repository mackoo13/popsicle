#!/bin/bash

while read -r path; do
    name=`basename "${path%.*}"`

    echo "Parsing $name"

    if grep -q struct "$path"; then
        echo "\tSkipping $name (struct detected)"
        continue
    fi

    python3 lore.py ${name}.c

done <<< `find ../kernels_lore/orig/ -iname '*44*.c'`
