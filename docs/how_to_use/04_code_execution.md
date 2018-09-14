## Code execution

_Note: code execution should be preceded by [code transformation](02_code_transformation.md)!_

Different scripts are used to execute the programs, depending on the purpose of collecting the data.

`$LORE_PROC_DIR` should point to the input directory. Each of its subdirectories contains the files needed to run the program:

```$xslt
$LORE_PROC_DIR/
├-- program1/  
|   ├-- program1.c
|   ├-- program1_max_params.txt
|   └-- program1_params_names.txt
├-- program2/  
├-- program3/
├   ...  
```

The results will be saved in `$PAPI_OUT_DIR`.

### Execution for time prediction

Usage: `./exec/exec.sh [output_file_name]`

Compiler: gcc

`output_file_name` should be provided without extension. The output will be saved to `$PAPI_OUT_DIR/time/[output_file_name].csv`.


### Execution for speedup prediction (GCC optimisation)

Runs the programs compiled with `-O0` and `-O3` [optimisation flags](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).

Usage: `./exec/exec_opt.sh [output_file_name]`

Compiler used: gcc

`output_file_name` should be provided without extension. The output will be saved to two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_O0.csv` (compiled with `-O0`)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_O3.csv` (compiled with `-O3`)


### Execution for speedup prediction (loop unrolling)

Used to collect data for speedup prediction (comparing the same programs with or without loop unrolling).

Usage: `./exec_clang/exec.sh [output_file_name]`

Compiler used: clang

`output_file_name` should be provided without extension. The output will be saved to two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_ur.csv` (unrolling enabled)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_nour.csv` (unrolling disabled)


