## LORE download

Programs from [LORE repository](https://vectorization.computer) must be downloaded in order to train the model.

### Prerequisites

To obtain the source codes from LORE, you will need the IDs of all available loops.

Wombat comes with a bundled list in `config/lore_loops.csv`.

To get an up-to-date list, you can download it from [LORE website](https://vectorization.computer/query.html) using the following query:

`SELECT id, application, benchmark, file, line, function, version FROM loops`


### Downloading the source codes

Usage: `python3 lore/download.py <path_to_csv_file>`