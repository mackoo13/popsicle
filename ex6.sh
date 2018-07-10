#!/bin/bash
# ./ex6 <out-file-name>

./obj.sh ex4

echo "PAPI_L1_DCM,PAPI_L1_ICM,PAPI_TOT_INS,PAPI_REF_CYC,time" > papi_output/$1.csv

for x in {100..15000..50}
do
    let "sq=$x*$x"
    echo $x
    echo "int max=$sq;" > kernels/kernel1_par.c
    ./ker.sh 1
    ./link.sh ex4
    ./ex4 >> papi_output/$1.csv
done