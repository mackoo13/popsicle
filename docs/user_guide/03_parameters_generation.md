# Parameters generation

In many programs it is possible to provide loop bounds on compilation time. In this step you can 


## Prerequisites

_Previous step: [code transformation](02_code_transformation.md)_

`$LORE_PROC_DIR` should point to the input directory. Each of its subdirectories contains the files needed to generate the parameters for one program (`(...)_params_names.txt` and `(...)_max_param.txt`):

    $LORE_PROC_DIR/
    ├-- program1/  
    |   ├-- program1.c
    |   ├-- program1_max_params.txt
    |   └-- program1_params_names.txt
    ├-- program2/  
    └-- program3/

the results will be saved to `(...)_params.txt` file in the same directory.


## Usage

### `popsicle-params-lore [n_params] [-u]`

#### `[n_params]`

Number of different parameters to generate

#### `[-u]`

Use this flag to use programs with loop unrolling (`$LORE_PROC_CLANG_PATH` directory). Otherwise, programs from `$LORE_PROC_PATH` will be used.


## Example

Input

```
// (...)_params_names.txt

PARAM_COUNT
```

```
// (...)_max_param.txt

265
```

Output

    // (...)_params.txt
    
    -D PARAM_COUNT=88
    -D PARAM_COUNT=176
    -D PARAM_COUNT=265


## Implementation details

### Values interpolation

The script attempts to generate such parameters values, that the execution time grows linearly. It is assumed that the number of variables corresponds to the complexity of the program.

For example, if there is only one parameter, we might expect linear time complexity. A possible result is `[2500, 5000, 7500, 10000]`. 

If two parameters are found, we might expect square time complexity. The output might be `50, 71, 87, 100]`, resulting in execution time approximately `[2500, 5000, 7500, 10000]`.


## Next step

You are now ready to [run your programs](04_code_execution.md) in batch and collect results.