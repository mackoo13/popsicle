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

### `popsicle-params-lore [n_values] [-u]`

#### `[n_values]`

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

Command

```
popsicle-params-lore 3
```

Output

    // (...)_params.txt
    
    -D PARAM_COUNT=88
    -D PARAM_COUNT=176
    -D PARAM_COUNT=265


## Next step

You are now ready to [run your programs](04_code_execution.md) in batch and collect results.