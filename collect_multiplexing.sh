#!/bin/bash
# ./collect_multiplexing.sh <out-file-name>

i=1
id=0
trials=5

./obj.sh exec_loop_multiplexing
echo -n "" > papi_output/$1.csv

while true
do
    if [ -e kernels/${i}/kernel.c ]
    then
        min=$(cat kernels/${i}/min.txt)
        max=$(cat kernels/${i}/max.txt)
        step=$(cat kernels/${i}/step.txt)

        for val in `seq ${min} ${step} ${max}`
        do
            sq=$((val*val))
            echo ${val}
            echo "int max=$sq;" > kernels/params.c
            ./ker.sh ${i}
            ./link.sh exec_loop_multiplexing

            for trial in `seq ${trials}`
            do
                echo -n ${id}, >> papi_output/$1.csv
                ./exec_loop_multiplexing >> papi_output/$1.csv
            done

            ((id++))
        done
    else
        break
    fi

    ((i++))
done

