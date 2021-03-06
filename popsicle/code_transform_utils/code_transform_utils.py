from __future__ import print_function
from functools import reduce
import numpy as np
import re
# noinspection PyPep8Naming
from typing import List, Tuple
from pycparser import c_ast

from popsicle.code_transform_utils.exceptions import ParseException
from popsicle.code_transform_utils.expr_estimator import ExprEstimator


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


# noinspection PyPep8Naming,PyMethodMayBeStatic
class ArrayDeclToPtrVisitor(c_ast.NodeVisitor):
    def __init__(self, dims):
        self.dims = dims

    def visit_FileAST(self, node):
        for i, item in enumerate(node.ext):
            if type(item) is not c_ast.Decl or type(item.type) is not c_ast.ArrayDecl:
                continue

            type_decl = item.type

            while type(type_decl) is c_ast.ArrayDecl:
                type_decl = type_decl.type

            dim = self.dims[type_decl.declname]

            decl_node = type_decl
            for _ in range(dim):
                decl_node = c_ast.PtrDecl([], decl_node)
            node.ext[i].type = decl_node


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
            s_eval = ExprEstimator().estimate(node.name.subscript)
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

            if type(left) is c_ast.ID:
                right_est = ExprEstimator(self.maxs).estimate(right)
                if len(right_est) > 0:
                    if left.name in self.maxs:
                        self.maxs[left.name].update(right_est)
                    else:
                        self.maxs[left.name] = right_est


# noinspection PyPep8Naming,PyMethodMayBeStatic
class CompoundInsertNextToVisitor(c_ast.NodeVisitor):
    """
    Used to insert nodes just before or after specific nodes.
    """
    def __init__(self, where, c_ast_type_name, items, properties=None):
        """
        :param where: 'before' or 'after'
        :param c_ast_type_name: Name of c_ast class, next to which new nodes will be added
        :param items: List of nodes to insert
        :param properties: A dictionary of attributes. Items will be inserted before/after a node only if it matches
                           all these properties.

        Examples:
            CompoundInsertNextToVisitor('before', 'Return, [node1, node2])
             - inserts node1 and node2 before each return statement

            CompoundInsertNextToVisitor('after', 'Pragma, [node1], properties={'string': 'scop'})
             - inserts node1 after each '#pragma scop'
        """
        if where not in ('before', 'after'):
            raise ValueError('CompoundInsertNextToVisitor: \'where\' must be wither \'before\' or \'after\'')

        self.properties = properties if properties is not None else {}
        self.c_ast_type_name = c_ast_type_name
        self.items = items
        self.where = where

    def visit_Compound(self, node):
        items = node.block_items
        old_items = items.copy()
        found_indices = []

        for i, item in enumerate(items):
            if type(item).__name__ == self.c_ast_type_name:
                properties_match = True
                for prop_k, prop_v in self.properties.items():
                    if not hasattr(item, prop_k) or getattr(item, prop_k) != prop_v:
                        properties_match = False

                if properties_match:
                    found_indices.append(i if self.where == 'before' else i + 1)

        while len(found_indices) > 0:
            i = found_indices.pop()
            items[i:i] = self.items

        for item in old_items:
            c_ast.NodeVisitor.generic_visit(self, item)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class DeclRemoveModifiersVisitor(c_ast.NodeVisitor):
    """
    Removes modifiers (e.g. 'extern') from variable declarations.
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
        depth: int

    Example:
        Input:
            code: '...
                for(...) {
                    for(...) {}
                }
                for(...) {} ...'
        Output:
            depth: 2
    """
    def __init__(self, depth=0):
        self.depth = depth
        self.result = depth

    def visit_For(self, node):
        # node.show()
        fdc = ForDepthCounter(self.depth + 1)
        fdc.visit(node.stmt)
        self.result = max(self.result, fdc.result)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class ForPragmaUnrollVisitor(c_ast.NodeVisitor):
    """
    Inserts PRAGMA(PRAGMA_UNROLL) above the innermost 'for' loop
    """
    def __init__(self, depth=0):
        self.depth = depth

    def visit_For(self, node):
        fpuv = ForPragmaUnrollVisitor(self.depth + 1)
        fpuv.visit(node.stmt)
        self.depth = max(self.depth, fpuv.depth)

        if self.depth == 1:
            if type(node.stmt) is c_ast.For:
                node.stmt = c_ast.Compound([node.stmt])

            if type(node.stmt) is c_ast.Compound:
                # note: this branch can also be called after c_ast.For case (above)
                items = node.stmt.block_items
                for_index = None

                for i, item in enumerate(items):
                    if type(item) is c_ast.For:
                        for_index = i

                if for_index is not None:
                    items.insert(for_index, pragma_unroll())


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
        nxt = node.next
        cond = node.cond

        if type(cond) is not c_ast.BinaryOp:
            raise ParseException('Unsupported format of for loop condition ("i < N" or alike expected)')

        if type(nxt) is not c_ast.UnaryOp and type(nxt) is not c_ast.Assignment:
            raise ParseException('Unsupported format of for loop increment (UnaryOp or Assignment expected)')

        if nxt.op not in ('p++', '++', '+=', 'p--', '--', '-='):
            raise ParseException(
                'Unsupported format of for loop increment ("++" or "+=" expected, "' + nxt.op + '" found)')

        counter = cond.left
        bound = cond.right
        bound_eval = ExprEstimator().estimate(bound)

        if type(counter) is not c_ast.ID:
            return

        if counter.name in self.maxs and len(bound_eval) > 0:
            self.maxs[counter.name].update(bound_eval)
        else:
            self.maxs[counter.name] = bound_eval

        id_visitor = IDVisitor()
        id_visitor.visit(bound)
        for nxt in id_visitor.names:
            self.bounds.add(nxt)

        c_ast.NodeVisitor.generic_visit(self, node)


# noinspection PyPep8Naming,PyPep8Naming
class FuncDefFindVisitor(c_ast.NodeVisitor):
    """
    Finds the declaration node of specified function
    """
    def __init__(self, name):
        self.name = name
        self.res = None

    def visit_FuncDef(self, node):
        if node.decl.name == self.name:
            self.res = node


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

        var_name = type_node.declname
        var_type = ' '.join(type_node.type.names)

        self.dtypes[var_name] = var_type


# noinspection PyPep8Naming,PyMethodMayBeStatic
class RemoveBoundDeclsVisitor(c_ast.NodeVisitor):
    """
    Removes declarations of all variables provided in 'names' list.
    """
    def __init__(self, names):
        self.names = names

    def visit_FileAST(self, node):
        i_to_remove = []
        for i, e in enumerate(node.ext):
            if type(e) is c_ast.Decl and e.name in self.names:
                i_to_remove.append(i)

        while len(i_to_remove) > 0:
            i = i_to_remove.pop()
            node.ext.pop(i)


# noinspection PyPep8Naming,PyMethodMayBeStatic
class ReturnIntVisitor(c_ast.NodeVisitor):
    """
    Changes all 'return;' statements without parameters to 'return 0;'.
    This usually follows a change of function type from 'void' to 'int'.
    """
    def __init__(self):
        pass

    def visit_Return(self, node):
        if type(node.expr) is not c_ast.Constant:
            node.expr = c_ast.Constant('int', '0')


# noinspection PyPep8Naming,PyMethodMayBeStatic
class SingleToCompoundVisitor(c_ast.NodeVisitor):
    """

    """
    def __init__(self):
        pass

    def generic_visit_loop(self, node):
        if type(node.stmt) is not c_ast.Compound:
            node.stmt = c_ast.Compound([node.stmt])

        self.generic_visit(node.stmt)

    def visit_DoWhile(self, node):
        self.generic_visit_loop(node)

    def visit_For(self, node):
        self.generic_visit_loop(node)

    def visit_If(self, node):
        if type(node.iftrue) is not c_ast.Compound:
            node.iftrue = c_ast.Compound([node.iftrue])
        if type(node.iffalse) is not c_ast.Compound:
            node.iffalse = c_ast.Compound([node.iffalse])

        self.generic_visit(node.iftrue)
        self.generic_visit(node.iffalse)

    def visit_While(self, node):
        self.generic_visit_loop(node)


# noinspection PyPep8Naming
class StructVisitor(c_ast.NodeVisitor):
    """
    Determines if the code contains struct. Structs are not supported during some code generation tasks - in such case,
    the program will be skipped.
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
        var_name = node.declname
        var_type = ' '.join(node.type.names)

        self.dtypes[var_name] = var_type


def build_decl(var_name: str, var_type: str) -> c_ast.Decl:
    type_decl = c_ast.TypeDecl(var_name, [], c_ast.IdentifierType([var_type]))
    return c_ast.Decl(var_name, [], [], [], type_decl, None, None)


def dtype_size(dtype):
    dtype = dtype.split(' ')[-1]    # signed, unsigned etc

    if dtype == 'char':
        return 1
    elif dtype in ('int', 'short'):
        return 2
    elif dtype == 'float':
        return 4
    elif dtype == 'double':
        return 8
    else:
        return 2


def exprs_prod(exprs: List[c_ast.Node]) -> c_ast.Node:
    """
    Product of a list of c_ast expressions
    :param exprs: Expressions
    :return: c_ast.Node representing the product
    """
    # noinspection PyTypeChecker
    return reduce(lambda a, b: c_ast.BinaryOp('*', a, b), exprs)


def exprs_sum(exprs: List[c_ast.Node], divide_long_expr=True) -> c_ast.Node:
    """
    Sum of a list of c_ast expressions
    :param divide_long_expr:
    :param exprs: Expressions
    :return: c_ast.Node representing the sum
    """
    if divide_long_expr and len(exprs) > 50:
        exprs_slices = np.split(np.array(exprs), range(50, len(exprs), 50))
        exprs = [exprs_sum(e, divide_long_expr) for e in exprs_slices]

    # noinspection PyTypeChecker
    return reduce(lambda a, b: c_ast.BinaryOp('+', a, b), exprs)


def loop_func_params():
    """
    Shorthand for 'int set, long_long* values, clock_t* begin, clock_t* end'
    """
    return c_ast.ParamList([
        build_decl('set', 'int'),
        build_decl('values', 'long_long*'),
        build_decl('begin', 'clock_t*'),
        build_decl('end', 'clock_t*'),
    ])


def papi_instr() -> Tuple[List[c_ast.Node], List[c_ast.Node]]:
    """
    :return: c_ast nodes representing the following code:
        exec(PAPI_start(set));
        *begin = clock();
        ...
        *end = clock();
        exec(PAPI_stop(set, values));
    """
    papi_start = c_ast.FuncCall(c_ast.ID('PAPI_start'), c_ast.ParamList([c_ast.ID('set')]))
    papi_stop = c_ast.FuncCall(c_ast.ID('PAPI_stop'),
                               c_ast.ParamList([c_ast.ID('set'), c_ast.ID('values')]))
    exec_start = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_start]))
    exec_stop = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_stop]))

    clock = c_ast.FuncCall(c_ast.ID('clock'), c_ast.ParamList([]))
    begin_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('begin')), clock)
    end_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('end')), clock)

    return [exec_start, begin_clock], [end_clock, exec_stop]


def pragma_unroll() -> c_ast.FuncCall:
    """
    :return: c_ast node representing the following code:
        PRAGMA(PRAGMA_UNROLL);
    """
    return c_ast.FuncCall(c_ast.ID('PRAGMA'), c_ast.ExprList([c_ast.ID('PRAGMA_UNROLL')]))


def remove_comments(code: str) -> str:
    """
    Removes comments from code to facilitate using pycparser.
    """
    code = re.sub('//.*\n|/\*.*\*/', '', code)  # greedy *?
    return code


def split_code(code: str) -> Tuple[str, str]:
    """
    Splits code into the section containing macros and the rest of the code.
    :param code: C code (as string)
    :return: Transformed code
    """
    includes, code = re.split(r'\n(?!(?:#|\s*\n))', code, 1)
    return includes, code
