from __future__ import print_function

from lore import lore_parser
import re
import sys
import os
import math


def malloc(name, dtype, sizes, dim):
    """
    Generates C code for array memory allocation and random initialization.
    For multidimensional arrays, the function is called recursively for each dimension.
    A constant of 2 is added to the size for safety.

    Example: malloc('A', 'int', ['N+42'], 0) -> A = malloc((N+42+2)*sizeof(int));
    :param name: Array name
    :param dtype: Array data type
    :param sizes: List of dimensions sizes (as strings)
    :param dim: Index of currently processed dimension
    :return: C code (as string)
    """
    size = sizes[dim]

    indices = ['i_' + str(n) for n in range(dim + 1)]
    indices_in_brackets = ['[' + i + ']' for i in indices]
    i = indices[-1]

    inds = ''.join(indices_in_brackets[:-1])
    ptr_asterisks = '*'*(len(sizes) - dim - 1)
    res = '\t' * dim
    res += '%s%s = malloc((%s+2) * sizeof(%s%s));\n' % \
           (name, inds, size, dtype, ptr_asterisks)
    res += '\t' * dim
    res += 'for(int %s=0; %s<%s+2; ++%s) {\n' % \
           (i, i, size, i)
    
    if dim < len(sizes) - 1:
        res += malloc(name, dtype, sizes, dim + 1)
    else:
        inds = ''.join(indices_in_brackets)
        res += '\t' * (dim + 1)
        res += '%s%s = (%s)rand();\n' % (name, inds, dtype)

    res += '\t' * dim + '}\n'

    return res


def gen_mallocs(bounds, refs, dtypes):
    """
    Generates a C code section containing all arrays' memory allocation and initialization.
    :param bounds:
    :param refs:
    :param dtypes: (map: array_name: str -> data type: str)
    :return:
    """
    res = ''
    for arr in refs:
        ref = refs[arr]

        if arr in dtypes:
            sizes = [lore_parser.max_set(size) for size in ref]
            sizes = [s for s in sizes if s is not None]
            if len(sizes) > 0:
                res += malloc(arr, dtypes[arr], sizes, 0)

    res = add_bounds_init(res, bounds)

    return res


def split_code(code):
    """
    Splits code into the section containing macros and the rest of the code.
    :param code: C code (as string)
    :return: Transformed code
    """
    return re.split(r'\n(?!#)', code, 1)


def add_includes(includes):
    """
    Adds all necessary #include instructions to the code.
    :param includes: C code section containing #include's (as string)
    :return: Transformed code
    """
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include <time.h>\n'
    res += '#include "' + os.path.abspath(os.path.dirname(sys.argv[0])) + '/../papi/papi_utils.h"\n'
    res += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'
    return res


def arr_to_ptr_decl(code, dtypes, dims):
    """
    Replaces all fixed-size array declarations with pointer declarations.

    Example; 'int A[42][42];' -> 'int** A;'
    :param code: C code (as string)
    :param dtypes: (map: array_name: str -> data type: str)
    :param dims: A map from fixed-length arrays to their dimensions (map: array_name: str -> data type: str[])
    :return: Transformed code
    """
    for arr in dims:
        code = re.sub(r'(' + dtypes[arr] + ')\s+(' + arr + ').*;', r'\1' + '*' * dims[arr] + ' ' + arr + ';', code)
    return code


def add_papi(code):
    """
    Adds PAPI instructions in the places indicated by #pragma.
    :param code: C code (as string)
    :return: Transformed code
    """
    code, scop_count = re.subn(r'(#pragma scop\s+)', r'\1exec(PAPI_start(set));\n*begin = clock();\n', code)
    code, endscop_count = \
        re.subn(r'(\s+#pragma endscop\s+)', r'\n*end = clock();\nexec(PAPI_stop(set, values));\1return 0;\n', code)

    if scop_count == 1 and endscop_count == 1:
        return code
    else:
        raise Exception('Exactly one "#pragma scop" and one "#pragma endscop" expected - found ' +
                        str(scop_count) + ' and ' + str(endscop_count) + ' correspondingly.')


def add_mallocs(code, mallocs):
    """
    Inserts generated arrays allocation and initialization section.
    :param code: C code (as string)
    :param mallocs: Generated C code (as string)
    :return: Transformed code
    """
    code = re.sub(r'(void loop\(\)\s*{)', r'\1\n\n' + mallocs, code)
    return code


def sub_loop_header(code):
    """
    Transforms the loop function header.
    :param code: C code (as string)
    :return: Transformed code
    """
    code, count = re.subn(r'void loop\(\)', 'int loop(int set, long_long* values, clock_t* begin, clock_t* end)', code)
    code = re.sub(r'return\s*;', 'return 0;', code)

    if count > 0:
        return code
    else:
        raise Exception('No "void loop()" function found')


def add_bounds_init(mallocs, bounds):
    """
    Inserts a fragment initializing program parameters into the code.
    The actual values should be injected at compilation time (-D option in gcc)
    :param mallocs: C code (as string)
    :param bounds:
    :return: Transformed code
    """
    inits = [n + ' = PARAM_' + n.upper() + ';' for n in bounds]
    inits = '\n'.join(inits)
    mallocs = inits + '\n\n' + mallocs
    return mallocs


def del_extern_restrict(code):
    """
    Remove 'extern' and 'restrict' keywords
    :param code: C code (as string)
    :return: Transformed code
    """
    code = re.sub(r'extern ', '', code)
    code = re.sub(r'restrict ', '', code)
    return code


def find_max_param(refs, ast, verbose=False):
    """
    Attempts to find the maximal value of program parameters. The upper bound is either imposed by limited memory
    (based on arrays dimensionality and their number) or loop count (based on for loop depth)

    if multiple parameters are present, all are assumed to be equal.
    :param refs:
    :param ast: AST tree
    :param verbose: True to print the output
    :return: The maximal parameter
    """
    max_arr_dim = max([len(refs) for refs in refs.values()])
    arr_count = len(refs)
    loop_depth = lore_parser.find_for_depth(ast)

    max_param_arr = math.pow(10000000 / arr_count, 1 / max_arr_dim)
    max_param_loop = math.pow(1000000000, 1 / loop_depth)
    max_param = min(max_param_arr, max_param_loop)

    if verbose:
        print('Max param: ', max_param)

    return max_param, max_arr_dim


def save_max_dims(proc_path, max_arr_dims):
    """
    todo
    :param proc_path:
    :param max_arr_dims:
    :return:
    """
    with open(proc_path + '/metadata.csv', 'w') as fout:
        fout.write('alg,max_dim\n')
        for alg, dim in max_arr_dims.items():
            fout.write(alg + ',' + str(dim) + '\n')
