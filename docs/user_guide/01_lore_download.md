# LORE download

Programs from [LORE repository](https://vectorization.computer) must be downloaded in order to train the model.

## Prerequisites

To obtain the source codes from LORE, you will need the IDs of all available loops.

Wombat comes with a bundled list in `config/lore_loops.csv`.

To get an up-to-date list, please use [LORE website](https://vectorization.computer/query.html) and the following query:

`SELECT id, application, benchmark, file, line, function, version FROM loops`


## Usage

### `wombat-lore-download [path_to_csv_file]`


## Implementation details

The files will be saved to `$LORE_ORIG_PATH`.

Each program will be named `lore_[file]_[line_number].c`.


## Next step

Once you have downloaded the source codes, you can proceed to [code transformation](02_code_transformation.md).