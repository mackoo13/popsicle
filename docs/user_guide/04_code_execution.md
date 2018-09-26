# Code execution

_Previous step: [parameters generation](03_parameters_generation.md)_

Remember to run the [configuration script](00_configuration.md)!

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

The results will be saved in `$OUT_DIR`.

## Usage

### `popsicle-exec.sh [mode] [output_file_name]`

#### `mode`

* `t` for execution time prediction
* `g` for GCC speedup prediction
* `u` for loop unrolling speedup prediction

#### `output_file_name`

Should be provided without extension. The output will be saved to:
* `$OUT_DIR/time/[output_file_name].csv` in `t` mode.


* `$OUT_DIR/gcc/[output_file_name]_O0.csv` (compiled with `-O0`) and `$OUT_DIR/gcc/[output_file_name]_O3.csv` (compiled with `-O3`) in `g` mode


* `$OUT_DIR/unroll/[output_file_name]_ur.csv` (unrolling enabled) and `$OUT_DIR/unroll/[output_file_name]_nour.csv` (unrolling disabled) in `u` mode


## Output

The output of the script in three modes will be saved into separate subdirectories of `$OUT_DIR`:

    $OUT_DIR
    ├-- gcc             // gcc mode
    ├-- time            // time mode
    ├-- predict   
    └-- unroll          // unroll mode
        
Output file format:

    alg, run, PAPI_EVENT_1, PAPI_EVENT_2, ..., PAPI_EVENT_n, time
    program1, -D N=100, 42, 434, ..., 65, 9.433
    program1, -D N=200, 80, 730, ..., 144, 22.563
    
Where `alg` is the program name, `run` are the parameters injected during compilation and `time` is the execution time in milliseconds.

## Next step

Now that you have collected the results, you can proceed to [training the model](05_training.md).
