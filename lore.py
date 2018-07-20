from pycparser import c_parser, c_ast
from functools import reduce
import re
import os
import argparse
import math


# noinspection PyPep8Naming
class ArrayRefVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_ArrayRef(self, node):
        n = node.name.name
        s = node.subscript

        # new refs to merge with the old ones
        refs = [{q(s, self.maxs)}]

        if type(node.name) is c_ast.ArrayRef:
            refs.append({q(node.name.subscript, self.maxs)})
            n = n.name

        if n in self.refs:
            for old_ref, new_ref in zip(self.refs[n], refs):
                old_ref.update(new_ref)
        else:
            self.refs[n] = refs


# noinspection PyPep8Naming
class AssignmentVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_Assignment(self, node):
        if node.op == '=':
            l = node.lvalue
            r = node.rvalue

            if type(l) is c_ast.ID:
                if l.name in self.maxs:
                    self.maxs[l.name].add(q(r, self.maxs))
                else:
                    self.maxs[l.name] = {q(r, self.maxs)}


# noinspection PyPep8Naming
class ForVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.maxs = {}
        self.bounds = set()
        self.loop_count = 0

    def visit_For(self, node):
        self.loop_count += 1
        c = node.cond
        if type(c) is not c_ast.BinaryOp:
            return

        v = c.left
        m = c.right

        if type(v) is not c_ast.ID:
            return

        if v.name in self.maxs:
            self.maxs[v.name].add(q(m))
        else:
            self.maxs[v.name] = {q(m)}

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


def max_set(s):
    return reduce( (lambda a, b: 'MAX(' + a + ', ' + b + ')'), s)


def q(n, maxs={}):
    if type(n) is str:
        return max_set(maxs[n]) if n in maxs else n
    if type(n) is c_ast.ID:
        return max_set(maxs[n.name]) if n.name in maxs else n.name
    elif type(n) is c_ast.BinaryOp:
        return q(n.left, maxs) + n.op + q(n.right, maxs)
    elif type(n) is c_ast.Constant:
        return n.value
    else:
        return '42'


def malloc(name, dtype, sizes):
    max_size = '*'.join(['('+s+')' for s in sizes])

    res = name + ' = malloc((' + max_size + ') * sizeof(' + dtype + '));\n'
    res += 'for(int i=0; i<' + max_size + ';++i) '
    res += name + '[i] = (' + dtype + ')rand();\n'

    """
    size = sizes.pop()
    res = name + ' = malloc((' + size + ') * sizeof(' + dtype + '*'*len(sizes) + '));\n'
    
    if len(sizes) > 0:
        ind = 'i_' + str(len(sizes))
        res += 'for(int ' + ind + '=0;' + ind + '<' + str(size) + ';++' + ind + ') {\n'
        res += malloc(name + '[' + ind + ']', dtype, sizes)
        res += '}\n'
    """
    return res


def gen_mallocs(ast, verbose=False):
    fv = ForVisitor()
    fv.visit(ast)
    if verbose:
        print('maxs: ', fv.maxs)
        print('bounds: ', fv.bounds)

    av = AssignmentVisitor(fv.maxs)
    av.visit(ast)
    if verbose:
        print('maxs: ', av.maxs)

    cv = ArrayRefVisitor(av.maxs)
    cv.visit(ast)
    if verbose:
        print('refs: ', cv.refs)

    pdv = PtrDeclVisitor()
    pdv.visit(ast)
    if verbose:
        print('dtypes: ', pdv.dtypes)

    res = ''
    for arr in cv.refs:
        if arr in pdv.dtypes:
            res += malloc(arr, pdv.dtypes[arr], [max_set(size) for size in cv.refs[arr]])

    res = add_bounds_init(res, fv.bounds)

    return res, fv.bounds, cv.refs, fv.loop_count


def split_code(code):
    return re.split(r'\n(?!#)', code, 1)


def add_includes(includes):
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include "../../../papi_utils/papi_events.h"\n'
    res += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'
    return res


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


def main():
    verbose = True

    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="File name")
    args = parser.parse_args()
    file = args.file_name
    file_name = file.split('.')[0]

    kernels_path = 'kernels_lore/'
    out_dir = kernels_path + 'proc/' + file_name

    with open(kernels_path + 'orig/' + file, 'r') as fin:
        code = fin.read()
        includes, code = split_code(code)

        parser = c_parser.CParser()
        ast = parser.parse(code)

        if verbose:
            ast.show()

        includes = add_includes(includes)
        mallocs, bounds, refs, loop_count = gen_mallocs(ast, verbose)
        code = del_extern_restrict(code)
        code = add_papi(code)
        code = add_mallocs(code, mallocs)
        code = sub_loop_header(code)
        code = includes + code

        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        with open(out_dir + '/' + file, 'w') as fout:
            fout.write(code)

        with open(out_dir + '/' + file_name + '_params.txt', 'w') as fout:

            if len(bounds) > 0:
                max_arr_dim = max([len(refs) for refs in refs.values()])
                arr_count = len(refs)

                max_param_arr = math.pow(10000000 / arr_count, 1 / max_arr_dim)
                max_param_loop = math.pow(100000000, 1 / loop_count)
                max_param = min(max_param_arr, max_param_loop)

                if verbose:
                    print('array count: ', arr_count)
                    print('loop count: ', loop_count)
                    print('max array dim: ', max_arr_dim)
                    print('max param: ', max_param)

                for k in range(1, 11):
                    defines = ['-D PARAM_' + b.upper() + '=' + str(int(k * max_param / 10)) for b in bounds]
                    fout.write(' '.join(defines) + '\n')


main()
