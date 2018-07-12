#!/bin/bash

name=2mm
name_papi=${name}_papi

# todo add explaining comments

sed 's/int main(int argc, char\*\* argv)/int loop(int set, long_long\* values)/g;
     s@#include <polybench.h>@#include <polybench.h>\n#include <papi.h>@g;
     s@polybench_prevent_dce@//polybench_prevent_dce@g;
     s@polybench_print_instruments@//polybench_print_instruments@g' kernels_pb/${name}.c > kernels_pb/${name_papi}.c

gcc -c \
    -I ~/papi/papi/src/ \
    -I ~/polybench-c-4.2.1-beta/utilities/ \
    kernels_pb/${name_papi}.c \
    -D MINI_DATASET \
    -o kernels_pb/${name_papi}.o

gcc -c \
    -I ~/papi/papi/src/ \
    exec_loop_pb.c

gcc kernels_pb/${name}.o \
    exec_loop_pb.o \
    papi_utils/papi_events.o \
    ~/polybench-c-4.2.1-beta/utilities/polybench.o  \
    -L ~/papi/papi/src/libpfm4/lib -lpfm \
    -L ~/papi/papi/src/ -lpapi \
    -static -o exec_loop_pb