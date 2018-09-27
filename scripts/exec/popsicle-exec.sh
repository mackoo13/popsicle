#!/usr/bin/env bash

# PARAMS:
#   $1 mode (t - time, g - gcc or u - unroll)
#   $2 output file name (without extension)


mode=$1
file_name=$2

if [[ ${mode} == "t" ]]; then
    popsicle-exec-time.sh $2
elif [[ ${mode} == "g" ]]; then
    popsicle-exec-gcc.sh $2
elif [[ ${mode} == "u" ]]; then
    popsicle-exec-unroll.sh $2
else
    echo "Available modes are: t (time), g (gcc) and u (unroll)."
    exit 1
fi
