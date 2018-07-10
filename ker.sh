#!/bin/bash
gcc -c kernels/params$1.c -I ~/papi/papi/src/ -o kernels/params.o
gcc -c kernels/kernel$1.c -I ~/papi/papi/src/ -o kernels/kernel.o
