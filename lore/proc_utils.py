from __future__ import print_function
from functools import reduce
import re
import os
# noinspection PyPep8Naming
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


# noinspection PyPep8Naming,PyMethodMayBeStatic
class CompoundInsertBeforeVisitor(c_ast.NodeVisitor):
    """
    todo
    todo what if contains another compound?
    """
    def __init__(self, c_ast_type_name, items):
        self.c_ast_type_name = c_ast_type_name
        self.items = items

    def visit_Compound(self, node):
        items = node.block_items
        indices = []

        for i, item in enumerate(items):
            if type(item).__name__ == self.c_ast_type_name:
                indices.append(i)

        # important: indices must be sorted in descending order to preserve indices while new items are inserted
        for i in indices[::-1]:
            items[i:i] = self.items

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class RemoveModifiersVisitor(c_ast.NodeVisitor):
    """
    todo
    """
    def __init__(self, modifiers_to_remove):
        self.modifiers_to_remove = modifiers_to_remove

    def visit_Decl(self, node):
        node.storage = [s for s in node.storage if s not in self.modifiers_to_remove]


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

        if self.res[0] == self.count + 1:
            if type(node.stmt) is c_ast.For:
                node.stmt = c_ast.Compound([node.stmt])

            if type(node.stmt) is c_ast.Compound:
                # note: can be also called after c_ast.For case (above)
                items = node.stmt.block_items
                for_index = None

                for i, item in enumerate(items):
                    if type(item) is c_ast.For:
                        for_index = i

                pragma = c_ast.FuncCall(c_ast.ID('PRAGMA'), c_ast.ExprList([c_ast.ID('PRAGMA_UNROLL')]))
                items.insert(for_index, pragma)

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

        if type(n) is not c_ast.UnaryOp and type(n) is not c_ast.Assignment:
            raise ParseException('Unknown format of for loop increment (UnaryOp or Assignment expected)')

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

        id_visitor = FindAllVarsVisitor()
        id_visitor.visit(m)
        for n in id_visitor.names:
            self.bounds.add(n)

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming,PyPep8Naming
class FindFuncVisitor(c_ast.NodeVisitor):
    """
    todo
    """
    def __init__(self, name):
        self.name = name
        self.main = None

    def visit_FuncDef(self, node):
        if node.decl.name == self.name:
            self.main = node
        

# noinspection PyPep8Naming
class FindAllVarsVisitor(c_ast.NodeVisitor):
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
class ArrType(c_ast.NodeVisitor):
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


# noinspection PyPep8Naming,PyMethodMayBeStatic
class SingleToCompoundVisitor(c_ast.NodeVisitor):
    """
    todo
    """
    def __init__(self):
        pass

    def visit_DoWhile(self, node):
        self.visit_For(node)

    def visit_For(self, node):
        if type(node.stmt) is not c_ast.Compound:
            node.stmt = c_ast.Compound([node.stmt])

    def visit_If(self, node):
        if type(node.iftrue) is not c_ast.Compound:
            node.iftrue = c_ast.Compound([node.iftrue])
        if type(node.iffalse) is not c_ast.Compound:
            node.iffalse = c_ast.Compound([node.iffalse])

    def visit_While(self, node):
        self.visit_For(node)


# noinspection PyPep8Naming
class StructVisitor(c_ast.NodeVisitor):
    """
    todo
    """
    def __init__(self):
        self.contains_struct = False

    # noinspection PyUnusedLocal
    def visit_Struct(self, node):
        self.contains_struct = True


# noinspection PyPep8Naming
class VarTypeVisitor(c_ast.NodeVisitor):
    """
    Used to determine the variables data types.

    Attributes:
        dtypes: Dict[str,str] - variable name -> data type
    """
    def __init__(self, dtypes):
        self.dtypes = dtypes

    def visit_TypeDecl(self, node):
        n = node.declname
        t = ' '.join(node.type.names)

        self.dtypes[n] = t


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


def build_decl(var_name, var_type):
    type_decl = c_ast.TypeDecl(var_name, [], c_ast.IdentifierType([var_type]))
    return c_ast.Decl(var_name, [], [], [], type_decl, None, None)


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


def gen_mallocs(refs, dtypes):
    """
    Generates a C code section containing all arrays' memory allocation and initialization.
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

    return res


def main_to_loop(node):
    """
    todo
    :param node:
    :return:
    """
    decl = node.decl
    body = node.body

    # todo move
    SingleToCompoundVisitor().visit(node)

    if decl.name == 'main':
        decl.name = 'loop'

        if type(decl.type) is c_ast.FuncDecl:
            decl.type.args = c_ast.ParamList([
                build_decl('set', 'int'),
                build_decl('values', 'long_long*'),
                build_decl('begin', 'clock_t*'),
                build_decl('end', 'clock_t*'),
            ])
            decl.type.type.declname = 'loop'

        if type(body) is c_ast.Compound:
            papi_start = c_ast.FuncCall(c_ast.ID('PAPI_start'), c_ast.ParamList([c_ast.ID('set')]))
            papi_stop = c_ast.FuncCall(c_ast.ID('PAPI_stop'),
                                       c_ast.ParamList([c_ast.ID('set'), c_ast.ID('values')]))
            exec_start = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_start]))
            exec_stop = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_stop]))

            clock = c_ast.FuncCall(c_ast.ID('clock'), c_ast.ParamList([]))
            begin_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('begin')), clock)
            end_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('end')), clock)

            body.block_items.insert(0, exec_start)
            body.block_items.insert(1, begin_clock)
            CompoundInsertBeforeVisitor('Return', [end_clock, exec_stop]).visit(body)


def malloc(name, dtype, sizes, dim):
    """
    Generates C code for array memory allocation and random initialization.
    For multidimensional arrays, the function is called recursively for each dimension.
    A constant of 2 is added to the size for safety.

    Example 1:
        malloc('A', 'int', ['N+42'], 0)
        ->
        A = malloc((N+42+2)*sizeof(int));
        for(int i_0=0; i_0<N+42+2; ++i_0) {
            A[i_0] = (int)rand();
        }

    Example 2:
        malloc('A', 'int', ['M', 'N'], 0)
        ->
        A = malloc((M+2)*sizeof(*int))
        for(int i_0=0; i_0<M+2; ++i_0) {
            A[i_0] = malloc((N+2)*sizeof(int))
            for(int i_0=0; i_0<N+2; ++i_0) {
                A[i_0][i_1] = (int)rand();
            }
        }

    todo check examples

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

    res += '\t' * dim
    res += '}\n'

    return res


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
        if n is not None and n.isdecimal():
            n_num = int(n)
            min_num = min(min_num, n_num)
            max_num = max(max_num, n_num)
        elif n is not None:
            s2.append(n)

    if max_num > 0:
        s2.append(str(max_num))
    if leave_min and min_num > 0 and min_num != max_num:
        s2.append(str(min_num))

    return s2


def remove_comments(code):
    """

    :param code:
    :return:
    """
    code = re.sub('//.*\n|/\*.*\*/', '', code)  # greedy *?
    return code


def remove_inline(code):
    """

    :param code:
    :return:
    """
    code = re.sub(' __inline__ ', ' ', code)
    return code


def save_max_dims(proc_path, max_arr_dims):
    """
    todo
    :param proc_path:
    :param max_arr_dims:
    :return:
    """
    with open(os.path.join(proc_path, 'metadata.csv'), 'w') as fout:
        fout.write('alg,max_dim\n')
        for alg, dim in max_arr_dims.items():
            fout.write(alg + ',' + str(dim) + '\n')


def split_code(code):
    """
    Splits code into the section containing macros and the rest of the code.
    :param code: C code (as string)
    :return: Transformed code
    """
    includes, code = re.split(r'\n(?!(?:#|\s*\n))', code, 1)
    return includes, code
