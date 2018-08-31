#!/usr/bin/env bash

for path in `find ${PIPS_PROC_PATH} -iname '*_preproc.c'`; do
    echo $path
    rm ${path}
done

for path in `find ${PIPS_PROC_PATH} -maxdepth 2 -iname '*.c' -not -iname '*_preproc.c' -not -iname '*_wombat.c'`; do
    if ! grep -q 'main(' "${path}"; then
        continue
    fi

    if ! grep -q 'for(' "${path}"; then
        continue
    fi

    name=${path: 0:-2}

    echo "Preprocessing ${name}"

    gcc -E ${path} \
        -I /home/maciej/pycparser/utils/fake_libc_include/ \
        -lm \
        -o ${name}_preproc.c
done
