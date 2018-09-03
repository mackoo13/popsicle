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
        sub = node.subscript

        # new refs to merge with the old ones
        refs = [{sub}]

        while type(node.name) is c_ast.ArrayRef:
            s_eval = estimate(node.name.subscript)
            if len(s_eval) > 0:
                refs.insert(0, s_eval)
            node = node.name

        var = node.name.name

        if var in self.refs:
            for old_ref, new_ref in zip(self.refs[var], refs):
                old_ref.update(new_ref)
        else:
            self.refs[var] = refs


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
                    self.maxs[left.name].update(right_est)
                else:
                    self.maxs[left.name] = right_est


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

        if v.name in self.maxs and len(m_eval) > 0:
            self.maxs[v.name].update(m_eval)
        else:
            self.maxs[v.name] = m_eval

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

    if type(n) is set or type(n) is list:
        options = []
        for ni in n:
            options.extend(estimate(ni, maxs, var, deps))

    elif type(n) is str:
        options = maxs[n] if n in maxs else [n]

    elif type(n) is c_ast.ID:
        if var is not None and n.name not in maxs:
            if var in deps:
                deps[var].add(n.name)
            else:
                deps[var] = {n.name}

        options = estimate(n.name, maxs, var, deps)

    elif type(n) is c_ast.BinaryOp:
        ls = estimate(n.left, maxs, var, deps)
        rs = estimate(n.right, maxs, var, deps)
        options = [eval_basic_op(l, n.op, r) for l in ls for r in rs]

    elif type(n) is c_ast.Constant:
        options = [n.value]

    else:
        options = []

    if len(deps) > 0:
        deps_values = reduce(lambda a, b: a | b, deps.values())
        raise ParseException('Variable-dependent array size detected: ' + ','.join(deps_values))

    options = remove_non_extreme_numbers(options)
    return set(options)


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
        if type(n) is str and n.isdecimal():
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
