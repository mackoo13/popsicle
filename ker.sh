#!/bin/bash
gcc -c kernels/params.c -I ~/papi/papi/src/ -o kernels/params.o
gcc -c kernels/$1/kernel.c -I ~/papi/papi/src/ -o kernels/kernel.o
