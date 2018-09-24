#!/usr/bin/env bash

# PARAMS:
#   $1 mode (t - time, g - gcc or u - unroll)
#   $2 output file name (without extension)


mode=$1
file_name=$2

if [[ ${mode} == "t" ]]; then
    popsicle-exec-time $2
elif [[ ${mode} == "g" ]]; then
    popsicle-exec-gcc $2
elif [[ ${mode} == "u" ]]; then
    popsicle-exec-unroll $2
else
    echo "Available modes are: t (time), g (gcc) and u (unroll)."
fi
