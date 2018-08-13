# Wombat

## Prerequisites

* python 3
* gcc

## Installation

```
cd wombat
pip install .
```

If you don't have `pip` installed, you can try using the following command instead:

```
python3 -m pip install .
```

## Preprocessing

The following scripts can be used to prepare data from LORE, train the model and persist it for future use.


### `lore_proc`

Usage: `./lore_proc.sh`

Transforms the source code of files from LORE repository to a runnable form, inserts PAPI instructions and execution time measurement.

The input files are taken from `LORE_ORIG_PATH` specified in config. Output will be saved in `LORE_PROC_PATH`.


### `lore_params`

Usage: `./lore_params.sh`

Generates a range of parameters for LORE programs. This step needs to be applied after `lore_proc`.

The directory containing files to process is specified in `LORE_PROC_PATH`. Result is saved in `<program_name>_params.txt` for each program.


### `lore_exec`

Usage: `./lore_exec.sh <output_file_name>`

This script executes all programs from `LORE_PROC_PATH` for all sets of parameters specified in `<program_name>_params.txt`.

The result, being a list of all runs with measured PAPI events, will be saved to `$PAPI_OUT_DIR/<output_file_name>.csv`.

Please be aware that for large number of programs and distinct parameters, it may take a few hours for this script to complete.


### `lore_exec_opt`

The usage is the same as `lore_exec`, but this script executes two versions of each program with different optimization flags: `-O0` and `-O3`.

The result will be saved to `$PAPI_OUT_DIR/<output_file_name>_O0.csv` and `$PAPI_OUT_DIR/<output_file_name>_O3.csv` for the two versions independently.


## Model training

### `lore_train`

Usage: `python3 lore/lore_train.py -i <input_file_path_1> -i <input_file_path_2> ...`

The input can be one or more `.csv` files obtained from `lore_exec`. The script will train a ML model to predict execution time and save it to `models` directory.

### `lore_train_opt`

Usage: `python3 lore/lore_train_opt.py -i <input_file_prefix_1> -i <input_file_prefix_2> ...`

Files `<input_file_prefix>_O0.csv` and `<input_file_prefix>_O3.csv` obtained from `lore_exec_opt` will be used as the input.

The script will train a ML model to predict speedup between `-O3` and `-O0` and save it to `models` directory.


## Prediction

Use these scripts to predict the execution time for new programs.

The code should conform to [this format](docs/file_format.md).


### `lore_predict`

Usage: `./lore_predict.sh <input_C_file_path>`

Compiles a C program, runs it, collects PAPI events and attempts to predict the execution time.

### `lore_predict_opt`

Usage: `./lore_predict_opt.sh <input_C_file_path>`

Compiles a C program, runs it, collects PAPI events and attempts to predict the speedup between `-O3` and `-O0`.
