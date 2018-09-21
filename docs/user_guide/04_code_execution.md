# Code execution

_Previous step: [parameters generation](03_parameters_generation.md)_

Different scripts are used to execute the programs, depending on the purpose of collecting the data.

`$LORE_PROC_DIR` should point to the input directory. Each of its subdirectories contains all files needed to run one program:

    $LORE_PROC_DIR/
    ├-- program1/  
    |   ├-- program1.c
    |   ├-- program1_max_params.txt
    |   ├-- program1_params.txt
    |   └-- program1_params_names.txt
    ├-- program2/  
    └-- program3/

The results will be saved in `$PAPI_OUT_DIR`.

## Usage (for time prediction)

###`./exec/exec.sh [output_file_name]`

`output_file_name` should be provided without extension. The output will be saved to `$PAPI_OUT_DIR/time/[output_file_name].csv`.

Compiler: gcc


## Usage (for GCC optimisation speedup prediction)

Runs the programs compiled with `-O0` and `-O3` [optimisation flags](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).

### `./exec/exec_opt.sh [output_file_name]`

####`[output_file_name]`
File name without extension. The output will be saved as two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_O0.csv` (compiled with `-O0`)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_O3.csv` (compiled with `-O3`)

Compiler: gcc


## Usage (for loop unrolling speedup prediction)

Used to collect data for speedup prediction (comparing the same programs with or without loop unrolling).

### `./exec_clang/exec.sh [output_file_name]`

#### `[output_file_name]` 
File name without extension. The output will be saved as two files: 

* `$PAPI_OUT_DIR/speedup/[output_file_name]_ur.csv` (unrolling enabled)
* `$PAPI_OUT_DIR/speedup/[output_file_name]_nour.csv` (unrolling disabled)

Compiler: clang


## Next step

Now that you have collected the results, you can proceed to [training the model](05_training.md).
