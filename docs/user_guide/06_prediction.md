# Prediction

The script 


## Prerequisites

_Previous step: [training a model transformation](05_training.md)_

Remember to run `source config/lore.cfg` first. It will populate the following environment variable:

- `$MODELS_DIR` - directory containing `.pkl` files with the [trained model](05_training.md)


## Usage: 

### `popsicle-predict [mode] [file_TODO]`

###`mode`
* `time` or `t` to predict execution time
* `gcc` or `g` to predict speedup between `-O0` and `-O3` 
* `unroll` or `u` to predict speedup after loop unrolling 

### `file_TODO`
TODO to your file. The required file format is presented below. Please make sure you conform to it or your file might be handled incorrectly by Popsicle.

## Input code format

There is no need to manually insert PAPI code into the file - Popsicle will take care of this! You only need keep in mind a couple of rules.

The desired code structure is based on files from LORE. It should always contain:
* `void loop()` function, which will be called by Popsicle during execution. 
* `#pragma scop` and `#pragma endscop` enclosing the code fragment you want to make measurements on.
* no libraries requiring special compilation flags (only `-lm` is supported)

Other functions can be defined if they are called inside `loop` (avoid using `main` though, as this will conflict with the `main` function in Popsicle).

    // includes
    // variables and arrays declaration
    
    void loop()
    {
        #pragma scop
    
        // loop kernel to be measured
    
        #pragma endscop
    }


## Example

    #include <stdio.h>
    #include <stdlib.h>
    int N;
    int* A;
    
    void loop()
    {
    
        N = 42;
        A = malloc(nr * sizeof(int));
    
        #pragma scop
        
        for(int i = 0; i < N; i++)
            A[i] += i;
                
        #pragma endscop
    }

## Execution scheme

Your program will be wrapped in the following scheme:

    void loop() {
        ...
        
        // start time counter
        // start PAPI counters
        # pragma scop
        
        ...
        
        # pragma endscop
        // stop and read PAPI counters
        // stop and read time counter
        
        ...
    }
    
    int main() {
        // initialise PAPI
    
        loop();
    
        // print the execution time and PAPI events 
    }