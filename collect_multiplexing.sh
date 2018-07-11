#!/bin/bash
# ./collect_multiplexing.sh <out-file-name>

i=1
./obj.sh exec_loop_multiplexing
echo "" > papi_output/$1.csv

while true
do
    if [ -e kernels/kernel$i.c ]
    then
        for val in {100..2000..50}
        do
            let "sq=$val*$val"
            echo $val
            echo "int max=$sq;" > kernels/params.c
            ./ker.sh $i
            ./link.sh exec_loop_multiplexing
            ./exec_loop_multiplexing >> papi_output/$1.csv
        done
    else
        break
    fi

    ((i++))
done

