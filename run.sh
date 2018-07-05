#!/bin/bash
gcc $1.c -I ~/papi/papi/src/ -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o $1 && ./$1
