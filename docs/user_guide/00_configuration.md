# Configuration

File `config/popsicle.cfg` should hold your configuration. Running this file will populate environment variables used in all scripts:

`source config/popsicle.cfg`

The template of the configuration file can be found in `config/popsicle.cfg.template`.


## Paths

- `PAPI_UTILS_PATH` - absolute path to this project's `papi` directory
- `OUT_DIR` - output directory for PAPI measurements
- `KERNEL_PATH` - root directory for `LORE_ORIG_PATH`, `LORE_PROC_PATH` and `LORE_PROC_CLANG_PATH`
- `MODELS_DIR` - output directory for ML models

It is recommended not to leave `LORE_ORIG_PATH`, `LORE_PROC_PATH` and `LORE_PROC_CLANG_PATH` unchanged, all being relative to `KERNEL_PATH`.