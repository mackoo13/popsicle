from functools import reduce
from pycparser import c_ast


class ParseException(Exception):
    pass


# noinspection PyPep8Naming
class ArrayDeclVisitor(c_ast.NodeVisitor):
    """
    Used to determine arrays' sizes and data types.
    Arrays declared as pointers with asterisk syntax are handled by PtrDeclVisitor.

    Attributes:
        dtypes: Dict[str,str] - variable name -> data type
        dims: Dict[str,List[int]] - variable name -> dimensions
    """
    def __init__(self, dtypes, dims):
        self.dtypes = dtypes
        self.dims = dims

    def visit_ArrayDecl(self, node):
        dim = 1

        while type(node.type) is c_ast.ArrayDecl:
            node = node.type
            dim += 1

        var = node.type.declname

        self.dims[var] = dim

        if type(node.type) is c_ast.TypeDecl:
            self.dtypes[var] = ' '.join(node.type.type.names)


# noinspection PyPep8Naming
class ArrayRefVisitor(c_ast.NodeVisitor):
    """
    For each array, the references are collected to approximate its maximal size.

    Attributes:
        refs: Dict[str,Set[str]] - array name -> encountered references
        maxs: Dict[str,Set[str]] - variable name -> possible maximal values

    Example:
        Input:
            array references in code: {'A[i]', 'A[i+1]', 'A[42]'}
            maxs: {'i': {'N'}}
        Output:
            refs: {'A': {'N', 'N+1', '42'}}
    """
    def __init__(self, refs, maxs):
        self.refs = refs
        self.maxs = maxs

    def visit_ArrayRef(self, node):
        var = node.name.name
        sub = node.subscript

        # new refs to merge with the old ones
        refs = [{sub}]

        while type(node.name) is c_ast.ArrayRef:
            s_eval = estimate(node.name.subscript)
            if s_eval is not None:
                refs.append({s_eval})
            node = node.name

        if var in self.refs:
            for old_ref, new_ref in zip(self.refs[var], refs):
                old_ref.update(new_ref)
        else:
            self.refs[estimate(var)] = refs


# noinspection PyPep8Naming
class AssignmentVisitor(c_ast.NodeVisitor):
    """
    Finds all variable assignments, treating their right sides as possible maximal values.
    The result is appended to existing maxs. Refs remain unchanged.
    An assumption is made that the assignments are processed in a proper order to handle dependencies between variables
        (see Example 2)

    Attributes:
        refs: Dict[str,Set[str]] - array name -> encountered references
        maxs: Dict[str,Set[str]] - variable name -> possible maximal values

    Example 1:
        Input:
            code: '... for(i=N-1; i>=0; --i) ...'
            refs: {}
            maxs: {'i': {'0'}, 'x': {'42'}}
        Output:
            maxs: {'i': {'N-1'}, 'x': {'42'}}

    Example 2:
        Input:
            code: '... for(i=0; i<N; ++i) for(j=i; j<M; ++j) ...'
            refs: {}
            maxs: {'i': {'N'}, 'j': {'M'}}
        After processing 'i=0':
            maxs: {'i': {'N', '0'}, 'j': {'M'}}
        Output:
            maxs: {'i': {'N', '0'}, 'j': {'M', 'N', '0'}}
    """
    def __init__(self, refs, maxs):
        self.refs = refs
        self.maxs = maxs

    def visit_Assignment(self, node):
        if node.op == '=':
            left = node.lvalue
            right = node.rvalue

            right_est = estimate(right, self.maxs)

            if type(left) is c_ast.ID and right_est is not None:
                if left.name in self.maxs:
                    self.maxs[left.name].add(right_est)
                else:
                    self.maxs[left.name] = {right_est}


# noinspection PyPep8Naming
class ForDepthCounter(c_ast.NodeVisitor):
    """
    Determines the maximal depth of nested for loops.

    Attributes:
        count: int - accumulative counter, for each loop being equal to the number of parent loops
        res: List[int, len=1] - result wrapped in a list to make it mutable

    Example:
        Input:
            code: '...
                for(...) {
                    for(...) {}
                }
                for(...) {} ...'
            res: [0]
        Output:
            res: [2]
    """
    def __init__(self, count, res):
        self.count = count
        self.res = res

    def visit_For(self, node):
        counter = ForDepthCounter(self.count + 1, self.res)
        counter.visit(node.stmt)
        self.res[0] = max(self.count, self.res[0])


# noinspection PyPep8Naming
class ForPragmaUnroll(c_ast.NodeVisitor):
    """
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
            items.insert(for_index, c_ast.Pragma('unroll'))
            print(items)

        self.res[0] = max(self.count, self.res[0])


# noinspection PyPep8Naming
class ForVisitor(c_ast.NodeVisitor):
    """
    Inspects for loops conditions to determine the maximal values of counter variables.

    Attributes:
        maxs: Dict[str,Set[str]] - [variable name] -> [set of possible maximal values]
        bounds: Set[str] - names of the variables needed to determine loop bounds. These variables are meant to be
            specified at compilation time.

    Example:
        Input:
            code: '... for(i=0; i<N+1; ++i) ...'
        Output:
            maxs: {'i': {'N+1'}}
            bounds: {'N'}
    """
    def __init__(self, maxs, bounds):
        self.maxs = maxs
        self.bounds = bounds

    def visit_For(self, node):
        n = node.next
        c = node.cond

        if type(c) is not c_ast.BinaryOp:
            raise ParseException('Unknown format of for loop condition ("i < N" or alike expected)')

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
    """
    Finds all variables used in an expression.

    Output:
        names: Set[string] - variables names
    """
    def __init__(self):
        self.names = set()

    def visit_ID(self, node):
        self.names.add(node.name)

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming
class PtrDeclVisitor(c_ast.NodeVisitor):
    """
    Used to determine the arrays data types.
    This visitor handles pointers declarations only. For bracket syntax declarations see ArrayDeclVisitor.

    Attributes:
        dtypes: Dict[str,str] - array name -> data type
    """
    def __init__(self, dtypes):
        self.dtypes = dtypes

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

    # noinspection PyUnusedLocal
    def visit_Struct(self, node):
        self.contains_struct = True


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

    maxs = {}
    refs = {}
    dims = {}
    dtypes = {}
    bounds = set()

    ForVisitor(maxs, bounds).visit(ast)

    AssignmentVisitor(refs, maxs).visit(ast)

    for var in maxs:
        maxs[var] = set(remove_non_extreme_numbers(maxs[var]))

    ArrayRefVisitor(refs, maxs).visit(ast)

    deps = {}
    for arr in refs:
        refs[arr] = [set([estimate(r, maxs, arr, deps) for r in ref]) for ref in refs[arr]]

    PtrDeclVisitor(dtypes).visit(ast)

    ArrayDeclVisitor(dtypes, dims).visit(ast)

    if verbose:
        print_debug_info(bounds, refs, dtypes, dims, maxs)

    return bounds, refs, dtypes, dims


def contains_struct2(ast):
    print(55)
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


def print_debug_info(bounds, refs, dtypes, dims, maxs):
    print('maxs: ', maxs)
    print('bounds: ', bounds)
    print('refs: ', refs)
    print('dtypes: ', dtypes)
    print('dims: ', dims)


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
