from __future__ import print_function
from pycparser import c_parser, c_ast
from functools import reduce
import re
import os
import argparse
import math


class ParseException(Exception):
    pass


# noinspection PyPep8Naming
class ArrayDeclVisitor(c_ast.NodeVisitor):
    def __init__(self, dtypes):
        self.dtypes = dtypes
        self.dims = {}

    def visit_ArrayDecl(self, node):
        dim = 1

        while type(node.type) is c_ast.ArrayDecl:
            node = node.type
            dim += 1

        n = node.type.declname

        self.dims[n] = dim

        if type(node.type) is c_ast.TypeDecl:
            self.dtypes[n] = ' '.join(node.type.type.names)


# noinspection PyPep8Naming
class ArrayRefVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_ArrayRef(self, node):
        n = node.name.name
        s = node.subscript

        # new refs to merge with the old ones
        refs = [{s}]

        while type(node.name) is c_ast.ArrayRef:
            s_eval = estimate(node.name.subscript)
            if s_eval is not None:
                refs.append({s_eval})
            node = node.name

        if n in self.refs:
            for old_ref, new_ref in zip(self.refs[n], refs):
                old_ref.update(new_ref)
        else:
            self.refs[estimate(n)] = refs


# noinspection PyPep8Naming
class AssignmentVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_Assignment(self, node):
        if node.op == '=':
            l = node.lvalue
            r = node.rvalue
            r_eval = estimate(r, self.maxs)

            if type(l) is c_ast.ID and r_eval is not None:
                if l.name in self.maxs:
                    self.maxs[l.name].add(r_eval)
                else:
                    self.maxs[l.name] = {r_eval}


# noinspection PyPep8Naming
class ForDepthCounter(c_ast.NodeVisitor):
    def __init__(self, count, res):
        self.count = count
        self.res = res      # max depth wrapped in an array to make it mutable

    def visit_For(self, node):
        counter = ForDepthCounter(self.count + 1, self.res)
        counter.visit(node.stmt)
        self.res[0] = max(self.count, self.res[0])


# noinspection PyPep8Naming
class ForVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.maxs = {}
        self.bounds = set()

    def visit_For(self, node):
        n = node.next
        c = node.cond

        if type(c) is not c_ast.BinaryOp:
            raise ParseException('Unknown format of for loop condition ("i < N" expected)')

        if type(n) is not c_ast.UnaryOp:
            print(type(n))
            raise ParseException('Unknown format of for loop increment (UnaryOp expected)')

        if n.op not in ('p++', '++', '+=', 'p--', '--', '-='):
            raise ParseException('Unknown format of for loop increment ("++" or "+=" expected, "' + n.op + '" found)')

        v = c.left
        m = c.right
        m_eval = estimate(m)

        if type(v) is not c_ast.ID:
            return

        if v.name in self.maxs and m_eval is not None:
            self.maxs[v.name].add(m_eval)
        else:
            self.maxs[v.name] = {m_eval}

        id_visitor = IDVisitor()
        id_visitor.visit(m)
        for n in id_visitor.names:
            self.bounds.add(n)

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming
class IDVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_ID(self, node):
        self.names.add(node.name)

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming
class PtrDeclVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.dtypes = {}

    def visit_PtrDecl(self, node):
        type_node = node.type

        while type(type_node) is c_ast.PtrDecl:
            type_node = type_node.type

        n = type_node.declname
        t = ' '.join(type_node.type.names)

        self.dtypes[n] = t


# noinspection PyPep8Naming
class StructVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.contains_struct = False

    def visit_Struct(self, node):
        self.contains_struct = True


def remove_non_extreme_numbers(s, leave_min=True):
    """
    Remove from an iterable all numbers which are neither minimal or maximal.
    The function leaves all non-numeric elements in the iterable untouched.
    The order of elements might be different in the output.

    Example: ['3', '6', 'N', '7'] -> ['N', '3', '7']
    :param s: Iterable of expressions as strings
    :param leave_min: If set to True, preserve minimal and maximum value from s. Otherwise, only maximum is preserved.
    :return: Transformed iterable
    """
    max_num = float('-inf')
    min_num = 0
    s2 = []

    for n in s:
        if n is not None:
            if n.isdecimal():
                n_num = int(n)
                if n_num > max_num:
                    max_num = n_num
                if n_num < min_num:
                    min_num = n_num
            else:
                s2.append(n)

    if max_num > 0:
        s2.append(str(max_num))
    if leave_min and min_num > 0 and min_num != max_num:
        s2.append(str(min_num))

    return s2


def max_set(s):
    """
    Transforms an iterable of expressions into a C expression which will evalueate to its maximum.
    MAX(x, y) macro must be included to the C program.
    If there are multiple integer values in the iterable, only the greatest one is preserved
    (see remove_non_extreme_numbers)

    Example: ['3', '6', '7', 'N', 'K'] -> 'MAX(MAX(7, N), 'K')'
    :param s: An iterable of expressions as strings
    :return: Output string
    """
    s2 = remove_non_extreme_numbers(s, leave_min=False)

    if len(s2) == 0:
        return None
    if len(s2) == 1:
        return s2[0]
    else:
        return reduce((lambda a, b: 'MAX(' + a + ', ' + b + ')'), s2)


def eval_basic_op(l, op, r):
    """
    Evaluate a basic arithmetic operation
    :param l: Left operand
    :param op: Operator
    :param r: Right operand
    :return: Result or a string representing the operation if it cannot be calculated
    """
    if l.isdecimal() and r.isdecimal():
        l_num = int(l)
        r_num = int(r)
        if op == '+':
            return str(l_num + r_num)
        if op == '-':
            return str(l_num - r_num)
        if op == '*':
            return str(l_num * r_num)

    return l + op + r


def estimate(n, maxs={}, var=None, deps={}):
    """
    Attempts to find the greatest value that an expression might have. The primary use of this function is determining
    the minimal size of an array based on the source code.
    If there is more than one expression that might be the maximum (e.g. variable-dependent or too complicated to be
    calculated here), all possible options are enclosed in MAX macro and left to be determined by C compiler.
    :param var:
    :param deps:
    :param n: An expression given as a c_ast object or a string
    :param maxs: A map containing possible upper bound of variables
    :return: C expression that will evaluate to the maximal possible value of the input expression.
    """
    options = estimate_options(n, maxs, var, deps)

    if len(deps) > 0:
        deps_values = reduce(lambda a, b: a | b, deps.values())
        raise ParseException('Variable-dependent array size detected: ' + ','.join(deps_values))

    options = remove_non_extreme_numbers(options)
    return max_set(options)


def estimate_options(n, maxs={}, var=None, deps={}):
    """
    Given an expression, this function attempts to find a list of possible expressions representing its upper bound.
    :param var: Name of the variable being estimated
    :param deps:
    :param n: An expression given as a c_ast object or a string
    :param maxs: maxs: A map containing possible upper bound of variables
    :return: List of expressions that might evaluate to the maximal possible value of the input expression.
    """
    if type(n) is str:
        return maxs[n] if n in maxs else [n]
    if type(n) is c_ast.ID:
        if var is not None and n.name not in maxs:
            if var in deps:
                deps[var].add(n.name)
            else:
                deps[var] = {n.name}

        return estimate_options(n.name, maxs, var, deps)
    elif type(n) is c_ast.BinaryOp:
        ls = estimate_options(n.left, maxs, var, deps)
        rs = estimate_options(n.right, maxs, var, deps)
        return [eval_basic_op(l, n.op, r) for l in ls for r in rs]
    elif type(n) is c_ast.Constant:
        return [n.value]
    else:
        return []


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
    res += '{%s}{%s} = malloc((%s+2) * sizeof(%s%s));\n' % \
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


def print_debug_info(bounds, refs, dtypes, dims, maxs):
    print('maxs: ', maxs)
    print('bounds: ', bounds)
    print('refs: ', refs)
    print('dtypes: ', dtypes)
    print('dims: ', dims)


def analyze(ast, verbose=False):
    """
    Extract useful information from AST tree
    :param ast: AST tree object
    :param verbose: If True, the output will be printed
    :return:
        res (string) - malloc instructions and array initialization)
        bounds () -
        refs () -
        dtypes (map: array_name: str -> data type: str)
        dims (map: array_name: str -> dimensions: int[])
    """

    fv = ForVisitor()
    fv.visit(ast)
    bounds = fv.bounds

    av = AssignmentVisitor(fv.maxs)
    av.visit(ast)
    maxs = av.maxs

    for var in maxs:
        maxs[var] = set(remove_non_extreme_numbers(maxs[var]))

    arv = ArrayRefVisitor(maxs)
    arv.visit(ast)
    refs = arv.refs

    deps = {}
    for arr in refs:
        refs[arr] = [set([estimate(r, maxs, arr, deps) for r in ref]) for ref in refs[arr]]

    pdv = PtrDeclVisitor()
    pdv.visit(ast)

    adv = ArrayDeclVisitor(pdv.dtypes)
    adv.visit(ast)
    dtypes = adv.dtypes
    dims = adv.dims

    if verbose:
        print_debug_info(bounds, refs, dtypes, dims, maxs)

    return bounds, refs, dtypes, dims


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
            sizes = [max_set(size) for size in ref]
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


def contains_struct(ast):
    sv = StructVisitor()
    sv.visit(ast)
    return sv.contains_struct


def add_includes(includes):
    """
    Adds all necessary #include instructions to the code.
    :param includes: C code section containing #include's (as string)
    :return: Transformed code
    """
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include <time.h>\n'
    res += '#include "../../../wombat/papi_utils/papi_events.h"\n'
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
    code = re.sub(r'(#pragma scop\n)', r'\1exec(PAPI_start(set));\n*begin = clock();', code)
    code = re.sub(r'(\n#pragma endscop\n)', r'\n*end = clock();\nexec(PAPI_stop(set, values));\1return 0;\n', code)
    return code


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
    code = re.sub(r'void loop\(\)', 'int loop(int set, long_long* values, clock_t* begin, clock_t* end)', code)
    code = re.sub(r'return\s*;', 'return 0;', code)
    return code


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


def find_for_depth(ast):
    """
    Finds the maximal depth of nested for loops.
    :param ast: AST tree
    :return: Max depth
    """
    res = [0]
    counter = ForDepthCounter(1, res)
    counter.visit(ast)
    return res[0]


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
    loop_depth = find_for_depth(ast)

    max_param_arr = math.pow(10000000 / arr_count, 1 / max_arr_dim)
    max_param_loop = math.pow(1000000000, 1 / loop_depth)
    max_param = min(max_param_arr, max_param_loop)

    if verbose:
        print('Max param: ', max_param)

    return max_param


def main():
    verbose = False

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("file_path", help="File path")
        parser.add_argument("proc_path", help="Proc path")
        args = parser.parse_args()
        file_path = args.file_path
        file_name = file_path.split('/')[-1]
        file_name = file_name.split('.')[0]
        proc_path = args.proc_path

        out_dir = proc_path + file_name

        with open(file_path, 'r') as fin:
            code = fin.read()
            includes, code = split_code(code)

            if contains_struct(code):
                raise ParseException('Code contains struct declaration.')

            parser = c_parser.CParser()
            ast = parser.parse(code)

            if verbose:
                ast.show()

            includes = add_includes(includes)

            bounds, refs, dtypes, dims = analyze(ast, verbose)
            mallocs = gen_mallocs(bounds, refs, dtypes)

            code = del_extern_restrict(code)
            code = arr_to_ptr_decl(code, dtypes, dims)
            code = add_papi(code)
            code = add_mallocs(code, mallocs)
            code = sub_loop_header(code)
            code = includes + code

            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

            if len(refs) == 0:
                raise ParseException('No refs found - cannot determine max_arr_dim')

            with open(out_dir + '/' + file_name + '.c', 'w') as fout:
                fout.write(code)

            max_param = find_max_param(refs, ast, verbose)
            with open(out_dir + '/' + file_name + '_max_param.txt', 'w') as fout:
                fout.write(str(int(max_param)))

            with open(out_dir + '/' + file_name + '_params_names.txt', 'w') as fout:
                fout.write(','.join(['PARAM_' + b.upper() for b in bounds]))

    except Exception as e:
        print('\t', e)


main()
