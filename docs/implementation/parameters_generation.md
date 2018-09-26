# Parameters generation

Many LORE programs have some variables which are not initialised - these are most often loop bounds (like `N` in `for(i=0; i<N; i++)`).

Popsicle initialises these variables at compilation time using `-D` option in GCC or Clang.


## Values interpolation

Popsicle attempts to generate the values of parameters in such way, that the execution time grows linearly. 

It is assumed that the complexity of the program is polynomial, as most of them contain nested loops. The degree of the polynomial is approximated by the number of variables.


## Examples

If there is only one parameter, we might expect linear time complexity. A possible result is `[2500, 5000, 7500, 10000]`. 

If two parameters are found, we might expect square time complexity. The output might be `50, 71, 87, 100]`, resulting in execution time approximately `[2500, 5000, 7500, 10000]`.
