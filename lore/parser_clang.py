from pycparser import c_ast


# noinspection PyPep8Naming
from parser import ForDepthCounter


class ForPragmaUnrollVisitor(c_ast.NodeVisitor):
    """
    Inserts PRAGMA(PRAGMA_UNROLL) above the innermost for loop
    """
    def __init__(self, count, res):
        self.count = count
        self.res = res

    def visit_For(self, node):
        counter = ForDepthCounter(self.count + 1, self.res)
        counter.visit(node.stmt)

        if self.res[0] == self.count + 1 and type(node.stmt) is c_ast.Compound:
            items = node.stmt.block_items
            for_index = None

            for i, item in enumerate(items):
                if type(item) is c_ast.For:
                    for_index = i
            items.insert(for_index, c_ast.FuncCall(c_ast.ID('PRAGMA'), c_ast.ExprList([c_ast.ID('PRAGMA_UNROLL')])))

        self.res[0] = max(self.count, self.res[0])


def add_pragma_unroll(ast):
    """

    :param ast: AST tree object
    :return:
    """
    res = [0]
    ForPragmaUnrollVisitor(1, res).visit(ast)
