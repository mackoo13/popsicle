#!/bin/bash
./obj.sh ex4

echo "PAPI_L1_DCM,PAPI_L1_ICM,PAPI_TOT_INS,PAPI_REF_CYC,time" > papi_output/o1.txt

for x in {100..500..100}
do
    let "sq=$x*$x"
    echo $x
    echo "int max=$sq;" > kernels/kernel1_par.c
    ./ker.sh 1
    ./link.sh ex4
    ./ex4 >> papi_output/o1.txt
done