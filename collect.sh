#!/bin/bash
# ./collect.sh <out-file-name>

i=1
./obj.sh exec_loop
echo "PAPI_L1_DCM,PAPI_L1_ICM,PAPI_TOT_INS,PAPI_REF_CYC,time" > papi_output/$1.csv

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
            ./link.sh exec_loop
            ./exec_loop >> papi_output/$1.csv
        done
    else
        break
    fi

    ((i++))
done

