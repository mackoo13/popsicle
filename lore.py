from pycparser import c_parser, c_ast
import re


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

    def visit_For(self, node):
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
        t = type_node.type.names[0]  # todo can there be more than 1?

        self.dtypes[n] = t


# noinspection PyPep8Naming
class DeclVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs, dtypes):
        self.maxs = maxs
        self.dtypes = dtypes
        self.bounds = []

    def visit_Decl(self, node):
        n = node.name
        t = node.type

        if type(t) is c_ast.TypeDecl and n not in self.maxs and n not in self.dtypes:
            self.bounds.append(n)


def max_set(s):
    return s.pop() if len(s) == 1 else 'max(' + ','.join(s) + ')'


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
    size = sizes.pop()
    res = name + ' = malloc((' + size + ') * sizeof(' + dtype + '*'*len(sizes) + '));\n'

    if len(sizes) > 0:
        ind = 'i_' + str(len(sizes))
        res += 'for(' + ind + '=0;' + ind + '<' + str(size) + ';++' + ind + ') {\n'
        res += malloc(name + '[' + ind + ']', dtype, sizes)
        res += '}\n'

    return res


def gen_mallocs(refs, dtypes):
    res = ''
    for arr in refs:
        if arr in dtypes:
            res += malloc(arr, dtypes[arr], [max_set(size) for size in refs[arr]])

    return res


def split_code(code):
    return re.split(r'\n(?!#)', code, 1)


def add_includes(includes):
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include "../../papi_utils/papi_events.h"\n'
    return res


def add_papi(code):
    code = re.sub(r'(#pragma scop\n)', r'\1exec(PAPI_start(set));\n', code)
    code = re.sub(r'(\n#pragma endscop)', r'\nexec(PAPI_stop(set, values));\1', code)
    return code


def add_mallocs(code, mallocs):
    code = re.sub(r'(void loop\(\)\s*{)', r'\1\n\n' + mallocs, code)
    return code


def sub_loop_header(code):
    code = re.sub(r'void loop()', 'int loop(int set, long_long* values)', code)
    return code


def main():
    with open('kernels_lore_OLD/k4/k4.txt', 'r') as fin:
        code = fin.read()
        includes, code = split_code(code)

        parser = c_parser.CParser()
        ast = parser.parse(code)

        ast.show()

        cv = ForVisitor()
        cv.visit(ast)
        print('maxs: ', cv.maxs)

        av = AssignmentVisitor(cv.maxs)
        av.visit(ast)
        print('maxs: ', av.maxs)

        cv = ArrayRefVisitor(av.maxs)
        cv.visit(ast)
        print('refs: ', cv.refs)

        pdv = PtrDeclVisitor()
        pdv.visit(ast)
        print('dtypes: ', pdv.dtypes)

        dv = DeclVisitor(av.maxs, pdv.dtypes)
        dv.visit(ast)
        print('bounds: ', dv.bounds)

        includes = add_includes(includes)
        mallocs = gen_mallocs(cv.refs, pdv.dtypes)
        code = add_papi(code)
        code = add_mallocs(code, mallocs)
        code = sub_loop_header(code)

        print(includes)
        print(code)


main()
