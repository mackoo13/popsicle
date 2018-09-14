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

## Usage

Training a model requires completing a couple of steps. Most of them need to be performed only once.

#### 0. Configuration ([read more](docs/user_guide/01_lore_download.md)) 
Specify paths to 

#### 1. Downloading source codes ([read more](docs/user_guide/01_lore_download.md)) 
Source codes from LORE repository are used to train a model.

#### 2. Code transformation ([read more](docs/user_guide/02_code_transformation.md)) 
The source codes need to be [transformed](docs/algorithm/lore_preprocessing.md) to enable PAPI measurements and generate missing code.

#### 3. Parameters generation ([read more](docs/user_guide/03_parameters_generation.md)) 
Many programs accept the loop bound as a parameter. Running the same program with different loop bounds lets us obtain more reliable data. 

In this step you determine how many different values should be tested.

#### 4. Code execution ([read more](docs/user_guide/04_code_execution.md)) 
All programs can be executed in batch a number of times to collect as much data as you need. 

#### 5. Training the model ([read more](docs/user_guide/05_training.md)) 
The collected data is used to train a prediction model. 

#### 6. Prediction ([read more](docs/user_guide/06_prediction.md)) 
Once you obtain a model, you can provide your own program to make predictions on.
