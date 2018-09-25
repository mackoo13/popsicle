# Configuration

File `config/popsicle.cfg` should hold your configuration. Running this file will populate environment variables used in all scripts:

`source config/popsicle.cfg`

The template of the configuration file can be found in `config/popsicle.cfg.template`.


## Paths

Before using Popsicle, you have to provide the paths for scripts and storing the data:

- `POPSICLE_ROOT` - absolute path to this project's root directory
- `OUT_DIR` - output directory for PAPI measurements
- `KERNEL_PATH` - root directory for `LORE_ORIG_PATH`, `LORE_PROC_PATH` and `LORE_PROC_CLANG_PATH`

Changing the remaining parameters is not recommended, but possible:

* `LORE_ORIG_PATH` - directory to save downloaded LORE programs
* `LORE_PROC_PATH` - directory to save transformed LORE programs
* `LORE_PROC_CLANG_PATH` - directory to save transformed LORE programs for loop unrolling
* `MODELS_DIR` - directory to save trained models
* `PAPI_UTILS_PATH`