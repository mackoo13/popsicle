## Code execution

### Simple execution

Used to collect data for execution time prediction.

Usage: `./exec/exec.sh [output_file_name]`

Compiler used: gcc

`output_file_name` should be provided without extension. The output will be saved to `$PAPI_OUT_DIR/time/[output_file_name].csv`.


### `-O0` and `-O3` execution

Used to collect data for speedup prediction (comparing `-O0` vs `-O3`).

Usage: `./exec/exec_opt.sh [output_file_name]`

Compiler used: gcc

`output_file_name` should be provided without extension. The output will be saved to two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_O0.csv` (compiled with `-O0`)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_O3.csv` (compiled with `-O3`)


### `#pragma unroll` and `#pragma nounroll` execution

Used to collect data for speedup prediction (comparing the same programs with or without loop unrolling).

Usage: `./exec_clang/exec.sh [output_file_name]`

Compiler used: clang

`output_file_name` should be provided without extension. The output will be saved to two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_ur.csv` (unrolling enabled)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_nour.csv` (unrolling disabled)


