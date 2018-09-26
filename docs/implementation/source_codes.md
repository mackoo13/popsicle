# Source codes for training

A large amount of data must be collected to train a model. To use performance counters, we need not only the source codes of programs, but also be able to execute them.


## LORE programs

Programs from [LORE repository](https://vectorization.computer) are used as the input for training the model.

However, the programs need to be executed to collect values of performance counters. This is not possible for LORE programs in their original form - allocation and initialization is missing.
    
    
## Code transformation

Popsicle attempts to generate missing code fragments and make the programs runnable. This includes:

* finding global parameters which need to be initialized to run the program, i.e. number of loop iterations. Their values are meant to be specified at compilation time.
* estimating necessary array sizes based on array references in code
* inserting `malloc` instructions and random array initialization
* enabling PAPI counters and execution time measurement


## Program before transformation

    // includes
    // variables and arrays declaration
    
    void loop()
    {
        #pragma scop
    
        // loop kernel to be measured
    
        #pragma endscop
    }


## Program after transformation

    // includes
    // variables and arrays declaration
    
    int loop(int set, long_long* values, clock_t* begin, clock_t* end)
    {
        // arrays allocation and initialization
    
        #pragma scop
        
        // start PAPI counters 
        // record begin time
    
        // loop kernel to be measured
        
        // record end time
        // stop PAPI counters
        
        #pragma endscop
    }
    
Note: A more detailed example is available in the [User Guide](../user_guide/02_code_transformation.md)
    

## Limitations

A number of assumptions has been made about the structure of supported programs. They are not sufficient to correctly parse all LORE programs, but cover a vast majority.

Files which do not satisfy these conditions are skipped in order to prevent incorrect code generation.

* simple format of loops is preferred (`for(i=0; i<N; i++)` or alike)
* operators `++`, `--`, `+=` and `-=` are also supported in loop increment
* no `struct` declarations are allowed

At the moment, about 50% of the programs from LORE database are correctly handled.