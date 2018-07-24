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
        refs = [{s}]    # todo: no q?

        while type(node.name) is c_ast.ArrayRef:
            s_eval = q(node.name.subscript)
            if s_eval is not None:
                refs.append({s_eval})
            node = node.name

        if n in self.refs:
            for old_ref, new_ref in zip(self.refs[n], refs):
                old_ref.update(new_ref)
        else:
            self.refs[q(n)] = refs  # todo: q?


# noinspection PyPep8Naming
class AssignmentVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_Assignment(self, node):
        if node.op == '=':
            l = node.lvalue
            r = node.rvalue
            r_eval = q(r, self.maxs)

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
            raise ParseException('Unknown format of for loop increment (UnaryOp expected)')

        if n.op not in ('p++', '++', '+='):
            raise ParseException('Unknown format of for loop increment ("++" or "+=" expected, "' + n.op + '" found)')

        v = c.left
        m = c.right
        m_eval = q(m)

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


def remove_small_numbers(s):
    max_num = float('-inf')
    s2 = []

    for n in s:
        if n.isdecimal():  # todo: do we need to handle negative numbers?
            if int(n) > max_num:
                max_num = int(n)
        else:
            s2.append(n)

    if max_num != float('-inf'):
        s2.append(str(max_num))

    return s2


def max_set(s):
    s2 = remove_small_numbers(s)

    if len(s2) == 0:
        return None
    if len(s2) == 1:
        return s2[0]
    else:
        return reduce((lambda a, b: 'MAX(' + a + ', ' + b + ')'), s2)


def eval_basic_op(l, op, r):
    print(l, op, r)
    try:
        l_num = int(l)
        r_num = int(r)
        if op == '+':
            return str(l_num + r_num)
        if op == '-':
            return str(l_num - r_num)
        if op == '*':
            return str(l_num * r_num)
    finally:
        pass

    return l + op + r


def q(n, maxs={}):
    if type(n) is str:
        return max_set(maxs[n]) if n in maxs else n
    if type(n) is c_ast.ID:
        return q(n.name, maxs)
    elif type(n) is c_ast.BinaryOp:
        print('bin', n.left, n.right)
        l = q(n.left, maxs)
        r = q(n.right, maxs)
        return eval_basic_op(l, n.op, r) if l is not None and r is not None else None
    elif type(n) is c_ast.Constant:
        return n.value
    else:
        return None


def q_arr(a, maxs={}):
    res = [q(n, maxs) for n in a]
    res = [r for r in res if r is not None]
    return res


def malloc(name, dtype, sizes, dim):
    size = sizes[dim]

    indices = ['i_' + str(n) for n in range(dim + 1)]
    indices_in_brackets = ['[' + i + ']' for i in indices]
    i = indices[-1]

    res = '\t' * dim + name + ''.join(indices_in_brackets[:-1]) + ' = malloc((' + size + '+1) * sizeof(' + dtype + '*'*(len(sizes) - dim - 1) + '));\n'
    res += '\t' * dim + 'for(int ' + i + '=0;' + i + '<' + str(size) + ';++' + i + ') {\n'
    
    if dim < len(sizes) - 1:
        res += malloc(name, dtype, sizes, dim + 1)
    else:
        res += '\t' * (dim + 1) + name + ''.join(indices_in_brackets) + ' = (' + dtype + ')rand();\n'

    res += '\t' * dim + '}\n'

    return res


def print_debug_info(bounds, refs, dtypes, dims, maxs):
    print('maxs: ', maxs)
    print('bounds: ', bounds)
    print('refs: ', refs)
    print('dtypes: ', dtypes)
    print('dims: ', dims)


def gen_mallocs(ast, verbose=False):
    """
    :param ast:
    :param verbose:
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
        maxs[var] = set(remove_small_numbers(maxs[var]))

    arv = ArrayRefVisitor(maxs)
    arv.visit(ast)
    refs = arv.refs

    for arr in refs:
        refs[arr] = [set(q_arr(r, maxs)) for r in refs[arr]]

    pdv = PtrDeclVisitor()
    pdv.visit(ast)

    adv = ArrayDeclVisitor(pdv.dtypes)
    adv.visit(ast)
    dtypes = adv.dtypes
    dims = adv.dims

    res = ''
    for arr in refs:
        ref = refs[arr]

        if arr in dtypes:
            sizes = [max_set(size) for size in ref]
            sizes = [s for s in sizes if s is not None]
            if len(sizes) > 0:
                res += malloc(arr, dtypes[arr], sizes, 0)

    res = add_bounds_init(res, bounds)

    if verbose:
        print_debug_info(bounds, refs, dtypes, dims, maxs)

    return res, bounds, refs, dtypes, dims


def split_code(code):
    return re.split(r'\n(?!#)', code, 1)


def add_includes(includes):
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include "../../../wombat/papi_utils/papi_events.h"\n'
    res += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'
    return res


def arr_to_ptr_decl(code, dtypes, dims):
    for arr in dims:
        code = re.sub(r'(' + dtypes[arr] + ')\s+(' + arr + ').*;', r'\1' + '*' * dims[arr] + ' ' + arr + ';', code)
    return code


def add_papi(code):
    code = re.sub(r'(#pragma scop\n)', r'\1exec(PAPI_start(set));\n', code)
    code = re.sub(r'(\n#pragma endscop\n)', r'\nexec(PAPI_stop(set, values));\1return 0;\n', code)
    return code


def add_mallocs(code, mallocs):
    code = re.sub(r'(void loop\(\)\s*{)', r'\1\n\n' + mallocs, code)
    return code


def sub_loop_header(code):
    code = re.sub(r'void loop\(\)', 'int loop(int set, long_long* values)', code)
    code = re.sub(r'return\s*;', 'return 0;', code)
    return code


def add_bounds_init(mallocs, bounds):
    inits = [n + ' = PARAM_' + n.upper() + ';' for n in bounds]
    inits = '\n'.join(inits)
    mallocs = inits + '\n\n' + mallocs
    return mallocs


def del_extern_restrict(code):
    code = re.sub(r'extern ', '', code)
    code = re.sub(r'restrict ', '', code)
    return code


def find_for_depth(ast):
    res = [0]
    counter = ForDepthCounter(1, res)
    counter.visit(ast)
    return res[0]


def find_max_param(refs, ast, verbose=False):
    max_arr_dim = max([len(refs) for refs in refs.values()])
    arr_count = len(refs)
    loop_depth = find_for_depth(ast)

    max_param_arr = math.pow(1000000 / arr_count, 1 / max_arr_dim)
    max_param_loop = math.pow(10000000, 1 / loop_depth)
    max_param = min(max_param_arr, max_param_loop)

    if verbose:
        print('Max param: ', max_param)

    return max_param


def main():
    verbose = True
    # verbose = False

    try:

        parser = argparse.ArgumentParser()
        parser.add_argument("file_name", help="File name")
        args = parser.parse_args()
        file = args.file_name
        file_name = file.split('.')[0]

        kernels_path = '../kernels_lore/'
        out_dir = kernels_path + 'proc/' + file_name

        with open(kernels_path + 'orig/' + file, 'r') as fin:
            code = fin.read()
            includes, code = split_code(code)

            parser = c_parser.CParser()
            ast = parser.parse(code)

            if verbose:
                ast.show()

            includes = add_includes(includes)

            mallocs, bounds, refs, dtypes, dims = gen_mallocs(ast, verbose)

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

            with open(out_dir + '/' + file, 'w') as fout:
                fout.write(code)

            with open(out_dir + '/' + file_name + '_params.txt', 'w') as fout:

                if len(bounds) > 0:
                    max_param = find_max_param(refs, ast, verbose)

                    for k in range(1, 11):
                        defines = ['-D PARAM_' + b.upper() + '=' + str(int(k * max_param / 10)) for b in bounds]
                        fout.write(' '.join(defines) + '\n')
                else:
                    fout.write('\n')

    except Exception as e:
        print('\t', e)


main()
