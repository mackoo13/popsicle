## CodeTransformer

### Constructor

#### `includes`

Part of the source code containing #include statements and macro definitions. It will not be parsed with pycparser and CodeTransformerAST, only with CodeTransformerStr             
    
#### `code`

The actual source code. Will be transformed both by CodeTransformerAST and CodeTransformerStr
                                
#### `papi_scope`

`'pragma'` if the fragment of code to make measurements on is enclosed in `#pragma scop` and `#pragma endscop`

`'function'` if you want PAPI to measure entire function body
        
#### `main_name`

Name of the main function. Defaults to `'main'`.

The function will be transformed to `int loop`.

#### `rename_bounds`

If set to `True`, all program parameters will be prepended with `PARAM_` prefix. 

This is only to improve the readability of the output code and indicate which variables should be set on compilation time.

Example:

```
//rename_bounds=False

for(int i=0; i<n; i++) { ... }
```

```
//rename_bounds=True

n = PARAM_N

for(int i=0; i<n; i++) { ... }
```

#### `add_pragma_unroll`

Inserts `PRAGMA(PRAGMA_UNROLL);` above the innermost loop.

The macro will be expanded to `#pragma PRAGMA_UNROLL` (`PRAGMA_UNROLL` should be provided on compilation time).

#### `gen_mallocs`

If set to `True`, the script will attempt to generate the code resposnsible for array allocation and initialisation. The main use is transorming LORE programs, in which this fragment is missing.

#### `modifiers_to_remove`

A list of modifiers that need to be removed from variable declarations. Examples include `extern` and `restrict` keywords.

#### `verbose`

If set to `True`, the AST tree and some debug info will be printed during transformation.


### Methods

### `transform(return_mode='all')`

Transforms and returns the code given in the constructor according to the configuration.

If `return_mode` is set to `'main'`, only the code of the main function is returned (the function to return is specified by `main_name` constructor parameter). Returns entire code otherwise.
