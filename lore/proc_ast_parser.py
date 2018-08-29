from functools import reduce
from pycparser import c_ast

from proc_visitors import StructVisitor, ArrayRefVisitor, ForVisitor, AssignmentVisitor, PtrDeclVisitor, \
    ArrayDeclVisitor, TypeDeclVisitor, ForDepthCounter, ForPragmaUnrollVisitor, CompoundVisitor


class ParseException(Exception):
    pass


def contains_struct(ast):
    sv = StructVisitor()
    sv.visit(ast)
    return sv.contains_struct


def estimate(n, maxs=None, var=None, deps=None):
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
    if maxs is None:
        maxs = {}

    if deps is None:
        deps = {}

    options = estimate_options(n, maxs, var, deps)

    if len(deps) > 0:
        deps_values = reduce(lambda a, b: a | b, deps.values())
        raise ParseException('Variable-dependent array size detected: ' + ','.join(deps_values))

    options = remove_non_extreme_numbers(options)
    return max_set(options)


def estimate_options(n, maxs=None, var=None, deps=None):
    """
    Given an expression, this function attempts to find a list of possible expressions representing its upper bound.
    :param var: Name of the variable being estimated
    :param deps:
    :param n: An expression given as a c_ast object or a string
    :param maxs: maxs: A map containing possible upper bound of variables
    :return: List of expressions that might evaluate to the maximal possible value of the input expression.
    """
    if maxs is None:
        maxs = {}

    if deps is None:
        deps = {}

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


def find_for_depth(ast):
    """
    Finds the maximal depth of nested for loops.
    :param ast: AST tree
    :return: Max depth
    """
    res = [0]
    ForDepthCounter(1, res).visit(ast)
    return res[0]


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


class ProcASTParser:
    def __init__(self, ast, verbose=False):
        self.maxs = {}
        self.refs = {}
        self.dims = {}
        self.dtypes = {}
        self.bounds = set()
        self.ast = ast
        self.verbose = verbose

        if verbose:
            ast.show()

        sv = StructVisitor()
        sv.visit(ast)
        if sv.contains_struct:
            print('\tSkipping - file contains struct')

    def add_pragma_unroll(self):
        """
        todo
        """
        res = [0]
        ForPragmaUnrollVisitor(1, res).visit(self.ast)
        if res[0] == 1:
            CompoundVisitor().visit(self.ast)

    def analyze(self, ast, verbose=False):
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

        ForVisitor(self.maxs, self.bounds).visit(ast)
        AssignmentVisitor(self.refs, self.maxs).visit(ast)

        for var in self.maxs:
            self.maxs[var] = set(remove_non_extreme_numbers(self.maxs[var]))

        ArrayRefVisitor(self.refs, self.maxs).visit(ast)

        deps = {}
        for arr in self.refs:
            self.refs[arr] = [set([estimate(r, self.maxs, arr, deps) for r in ref]) for ref in self.refs[arr]]

        PtrDeclVisitor(self.dtypes).visit(ast)
        ArrayDeclVisitor(self.dtypes, self.dims).visit(ast)
        TypeDeclVisitor(self.dtypes).visit(ast)

        self.bounds.difference_update(self.refs.keys())

        if verbose:
            self.print_debug_info()

    def print_debug_info(self):
        print('maxs: ', self.maxs)
        print('bounds: ', self.bounds)
        print('refs: ', self.refs)
        print('dtypes: ', self.dtypes)
        print('dims: ', self.dims)
