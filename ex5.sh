#!/bin/bash

i=1

while true
do
    if [ -e kernels/kernel$i.c ]
    then
        echo $i
    else
        break
    fi

    ((i++))
done