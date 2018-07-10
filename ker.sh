#!/bin/bash
gcc -c kernels/kernel$1_par.c -I ~/papi/papi/src/ -o kernels/kernel_par.o
gcc -c kernels/kernel$1.c -I ~/papi/papi/src/ -o kernels/kernel.o
