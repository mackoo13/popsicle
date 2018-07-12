#!/bin/bash
# ./collect_multiplexing.sh <out-file-name>

readonly trials=5
readonly out_file=papi_output/$1.csv

i=1
id=0

./obj.sh exec_loop_multiplexing
echo -n "" > ${out_file}

while true
do
    kernel_path=kernels/${i}

    if [ -e kernels/${i}/kernel.c ]
    then

        min=$(cat ${kernel_path}/min.txt)
        max=$(cat ${kernel_path}/max.txt)
        step=$(cat ${kernel_path}/step.txt)
        if [ -e kernels/${i}/flags.txt ]
        then
            flags=$(cat ${kernel_path}/flags.txt)
        else
            flags=""
        fi

        for val in `seq ${min} ${step} ${max}`
        do
            sq=$((val*val))
            echo ${val}
            echo "int max=$sq;" > kernels/params.c
            ./ker.sh ${i}
            gcc exec_loop_multiplexing.o papi_utils/papi_events.o kernels/params.o kernels/kernel.o \
                -L ~/papi/papi/src/libpfm4/lib -lpfm \
                -L ~/papi/papi/src/ -lpapi \
                ${flags} -static -o exec_loop_multiplexing

            for trial in `seq ${trials}`
            do
                echo -n ${id}, >> ${out_file}
                ./exec_loop_multiplexing >> ${out_file}
            done

            ((id++))
        done
    else
        break
    fi

    ((i++))
done

