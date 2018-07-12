#!/bin/bash

gcc $1.o papi_utils/papi_events.o kernels/params.o kernels/kernel.o -L ~/papi/papi/src/libpfm4/lib -lpfm  -L ~/papi/papi/src/ -lpapi -static -o $1
