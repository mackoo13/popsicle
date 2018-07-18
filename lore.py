from pycparser import c_parser, c_ast


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


def malloc(name, dtype, size):
    return name + ' = malloc((' + size + ') * sizeof(' + dtype + '));'


# noinspection PyPep8Naming
class ArrayRefVisitor(c_ast.NodeVisitor):
    def __init__(self, maxs):
        self.refs = {}
        self.maxs = maxs

    def visit_ArrayRef(self, node):
        n = node.name.name
        s = node.subscript

        if n in self.refs:
            self.refs[n].add(q(s, self.maxs))
        else:
            self.refs[n] = {q(s, self.maxs)}


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
        n = node.type.declname
        t = node.type.type.names[0]  # todo can there be more than 1?

        self.dtypes[n] = t


def main():
    with open('kernels_lore/k4/k4.txt', 'r') as fin:
        code = fin.read()
        parser = c_parser.CParser()
        ast = parser.parse(code)

        ast.show()

        cv = ForVisitor()
        cv.visit(ast)
        print(cv.maxs)

        cv = AssignmentVisitor(cv.maxs)
        cv.visit(ast)
        print(cv.maxs)

        cv = ArrayRefVisitor(cv.maxs)
        cv.visit(ast)
        print(cv.refs)

        pdv = PtrDeclVisitor()
        pdv.visit(ast)
        print(pdv.dtypes)

        for arr in cv.refs:
            if arr in pdv.dtypes:
                m = malloc(arr, pdv.dtypes[arr], max_set(cv.refs[arr]))
                print(m)



main()
