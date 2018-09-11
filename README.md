# Wombat

## Prerequisites

* [Python 3](https://www.python.org/)
* [GCC](https://gcc.gnu.org/)
* [PAPI](http://icl.utk.edu/papi/software/)

Note: if you encounter `perf_event support disabled by Linux with paranoid=3` using PAPI, run the following command to change the settings:
 
`sudo sh -c 'echo kernel.perf_event_paranoid=1 > /etc/sysctl.d/local.conf'`

## Installation

```
git clone https://github.com/mackoo13/wombat.git
cd wombat
pip3 install .
```

If you don't have `pip3` installed, you can try a workaround:

```
python3 -m pip install .
```

## LORE download

To obtain the set of programs from LORE repository, you must first download a CSV file with a list of currently available loops. Use [LOOP website](https://vectorization.computer/query.html) and the following query:

`SELECT id, application, benchmark, file, line, function, version FROM loops`

A pre-downloaded file is available in `config/lore_loops.csv`.

Usage: `python3 lore/download.py <path_to_csv_file>`

## Preprocessing

The following scripts can be used to prepare data from LORE, train the model and persist it for future use.


### `proc`

Usage: `python3 lore/proc.py`

Transforms the source code of files from LORE repository to a runnable form, inserts PAPI instructions and execution time measurement.

The input files are taken from `LORE_ORIG_PATH` specified in config. Output will be saved in `LORE_PROC_PATH`.


### `params`

Usage: `python3 lore/params.py <n_params>`

Generates a range of parameters for LORE programs. This step needs to be applied after `proc`.

`<n_params>` is the number of distinct parameters to generate (thus, the number of samples that will be produced by this program).

The directory containing files to process is specified in `LORE_PROC_PATH`. Result is saved in `<program_name>_params.txt` for each program.


## Programs execution

### `exec`

Usage: `./scripts/exec/exec.sh <output_file_name>`

This script executes all programs from `LORE_PROC_PATH` for all sets of parameters specified in `<program_name>_params.txt`.

The result, being a list of all runs with measured PAPI events, will be saved to `$PAPI_OUT_DIR/<output_file_name>.csv`.

Please be aware that for large number of programs and distinct parameters, it may take a few hours for this script to complete.


### `exec_opt`

The usage is the same as `exec`, but this script executes two versions of each program with different optimization flags: `-O0` and `-O3`.

The result will be saved to `$PAPI_OUT_DIR/<output_file_name>_O0.csv` and `$PAPI_OUT_DIR/<output_file_name>_O3.csv` for the two versions independently.


## Model training

### `train`

Usage: `python3 lore/train.py -i <input_file_path_1> -i <input_file_path_2> ...`

The input can be one or more `.csv` files obtained from `exec`. The script will train a ML model to predict execution time and save it to `models` directory.

### `train_opt`

Usage: `python3 lore/train_opt.py -i <input_file_prefix_1> -i <input_file_prefix_2> ...`

Files `<input_file_prefix>_O0.csv` and `<input_file_prefix>_O3.csv` obtained from `exec_opt` will be used as the input.

The script will train a ML model to predict speedup between `-O3` and `-O0` and save it to `models` directory.


## Prediction

Use these scripts to predict the execution time for new programs.

The code should conform to [this format](docs/scripts/input_code.md). An example is available in `examples/kernel.c`.


### `predict`

Usage: `./scripts/ml/predict.sh <input_C_file_path>`

Compiles a C program, runs it, collects PAPI events and attempts to predict the execution time.

### `predict_opt`

Usage: `./scripts/ml/predict_opt.sh <input_C_file_path>`

Compiles a C program, runs it, collects PAPI events and attempts to predict the speedup between `-O3` and `-O0`.
