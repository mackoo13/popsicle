# Training

## Prerequisites

_Previous step: [code execution](04_code_execution.md)_

Remember to run the [configuration script](00_configuration.md)!

As an input, you should provide one or more `.csv` files obtained by [executing](04_code_execution.md) programs in batch.


## Usage

### `popsicle-train [mode] -i [file_name]`

#### `[mode]`
 * `time` or `t` for execution time prediction
 * `gcc` or `g` for predicting speedup after gcc optimisation
 * `unroll` or `u` for predicting speedup after clang loop unrolling.
 
#### `-i [file_name]`

Input file name. You can specify multiple files by repeating this argument (i.e. `-i file1 -i file2 ...`).

There is no need to provide a full path, as it is loaded from the config (`$OUT_DIR`).

Please note that a name _without_ exception is expected. Providing an extension might lead to errors.


## Example

`popsicle-train gcc -i file1` will load data from `$OUT_DIR/gcc/file1_O0.csv` and `$OUT_DIR/gcc/file1_O3.csv` and train a model to predict a speedup between `-O0` and `-O3`.


## Next step

You can finally use the model for [prediction](06_prediction.md).