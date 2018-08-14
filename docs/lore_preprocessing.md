# Wombat

## LORE repository

Programs from [LORE repository](https://vectorization.computer) are used as the input for Machine Learning 

## Lore Parser

LORE source codes are missing array allocation and initialization. This script attempts to generate missing code and make it runnable by Wombat. This includes:

* finding global parameters which need to be initialized to run the program, i.e. number of loop iterations. Their values are meant to be specified at compilation time.
* estimating necessary array sizes based on array references in code
* inserting `malloc` instructions and random array initialization
* enabling PAPI counters and execution time measurement

#### Limitations

A number of assumptions has been made on the supported programs. They are not sufficient to correctly parse all LORE programs, but cover a vast majority.

Files which do not satisfy these conditions are skipped in order to prevent incorrect code generation

* simple `for` loops conditions, i.e. variable name, operator (`<`, `<=`, `>` or `>=`) and an expression
* simple `for` loops increments: `++`, `--`, `+=` and `-=` operators are supported
* no struct declarations

#### LORE file format

```$xslt
// includes
// variables and arrays declaration

void loop()
{
#pragma scop

    // loop kernel to be measured

#pragma endscop
}
```

#### Output format

```$xslt
// includes
// variables and arrays declaration

int loop(int set, long_long* values, clock_t* begin, clock_t* end)
{
    // global parameters initialization
    // arrays allocation and initialization

#pragma scop
exec(PAPI_start(set));
*begin = clock();

    // loop kernel to be measured
    
*end = clock();
exec(PAPI_stop(set, values));
#pragma endscop
}
```