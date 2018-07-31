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

## Training the model

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

Usage: `./lore_exec.sh <output_file_path>`,

This script executes all programs from `LORE_PROC_PATH` for all sets of parameters specified in `<program_name>_params.txt`.

The result, being a list of all runs with measured PAPI events, will be saved to `<output_file_path>.csv`.

Please be aware that for large number of programs and distinct parameters, it may take a few hours for this script to complete.


### `lore_train`

Usage: `python3 lore_train.py -i <input_file_path_1> -i <input_file_path_2> ...`

The input can be one or more `.csv` files obtained from `lore_exec`. The script will train a ML model to predict execution time and save it to `models` directory.


## Prediction

Use these scripts to predict the execution time for new programs.

The code should conform to this (todo: link to description) format.


### `lore_predict`

Usage: `./lore_predict.sh <input_C_file_path>`

Compiles a C program, runs it, collects PAPI events and attempts to predict the execution time.