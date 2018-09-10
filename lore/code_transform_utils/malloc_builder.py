from typing import List

from pycparser import c_ast
from code_transform_utils.code_transform_utils import remove_non_extreme_numbers, exprs_prod


def max_set(exprs):
    """
    Transforms an iterable of expressions into a C expression which will evalueate to its maximum.
    MAX(x, y) macro must be included to the C program.
    If there are multiple integer values in the iterable, only the greatest one is preserved
    (see remove_non_extreme_numbers)

    Example: ['3', '6', '7', 'N', 'K'] -> 'MAX(MAX(7, N), 'K')'
    :param exprs: An iterable of expressions as strings
    :return: Output string
    """

    # noinspection PyShadowingNames
    def max_set_recur(exprs):
        if len(exprs) == 0:
            return None
        if len(exprs) == 1:
            return exprs[0]
        else:
            half = int(len(exprs) / 2)
            a = max_set_recur(exprs[:half])
            b = max_set_recur(exprs[half:])
            return c_ast.FuncCall(c_ast.ID('MAX'), c_ast.ExprList([a, b]))
    
    if type(exprs) is str:
        return c_ast.ID(exprs)

    exprs = remove_non_extreme_numbers(exprs, leave_min=False)
    exprs = [c_ast.ID(e) for e in exprs]

    return max_set_recur(exprs)


class MallocBuilder:
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

    todo check

    :param name: Array name
    :param dtype: Array data type
    :param sizes: List of dimensions sizes (as strings)
    :return: C code (as string)
    """

    def __init__(self, name, dtype, sizes, initialiser='rand'):
        self.name = name
        self.dtype = c_ast.ID(dtype)
        self.sizes = [max_set(s) for s in sizes]
        self.initialiser = self.__polybench_init if initialiser == 'polybench' else self.__rand_init
        self.counter_prefix = 'i_' if not name.startswith('i_') else 'i_' + name

    def generate(self) -> List[c_ast.Node]:
        return [
            self.__malloc_assign(0),
            self.__for_loop(0)
        ]

    # PRIVATE MEMBERS

    def __array_ref(self, subs: List[c_ast.Node]) -> c_ast.Node:
        """
        todo
        :param subs:
        :return:
        """
        if len(subs) == 0:
            return c_ast.ID(self.name)
        else:
            sub = subs[-1]
            return c_ast.ArrayRef(self.__array_ref(subs[:-1]), sub)

    def __for_loop(self, depth: int) -> c_ast.For:
        """
        todo
        :param depth:
        :return:
        """
        i = self.counter_prefix + str(depth)
        init = c_ast.DeclList([c_ast.Decl(
            c_ast.ID(i), [], [], [],
            c_ast.TypeDecl(i, [], c_ast.IdentifierType(['int'])),
            c_ast.Constant('int', '0'), ''
        )])
        cond = c_ast.BinaryOp('<', c_ast.ID(i), self.sizes[depth])
        nxt = c_ast.Assignment('++', c_ast.ID(i), None)
        stmt = c_ast.Compound([])

        if depth < len(self.sizes) - 1:
            stmt.block_items = [self.__malloc_assign(depth + 1), self.__for_loop(depth + 1)]
        else:
            stmt.block_items = [self.initialiser(depth + 1)]

        return c_ast.For(init, cond, nxt, stmt)

    def __malloc(self, depth: int) -> c_ast.FuncCall:
        """
        todo
        :param depth:
        :return:
        """
        size_expr = \
            c_ast.BinaryOp(
                '+',
                self.sizes[depth],
                c_ast.Constant('int', '2')
            )

        sizeof = \
            c_ast.FuncCall(
                c_ast.ID('sizeof'),
                c_ast.ExprList([c_ast.ID(self.dtype.name + '*' * (len(self.sizes) - depth - 1))])   # todo proper Ptr
            )

        arg = c_ast.BinaryOp('*', size_expr, sizeof)

        return c_ast.FuncCall(c_ast.ID('malloc'), c_ast.ExprList([arg]))

    def __malloc_assign(self, depth: int) -> c_ast.Node:
        """
        todo
        :param depth:
        :return:
        """
        subs = self.__subs(depth)
        return c_ast.Assignment('=', self.__array_ref(subs), self.__malloc(depth))

    def __polybench_init(self, depth: int) -> c_ast.Node:
        """
        todo
        :param depth:
        :return:
        """
        subs = self.__subs(depth)
        left = self.__array_ref(subs)

        right = \
            c_ast.Cast(
                self.dtype,
                c_ast.BinaryOp('/',
                               c_ast.BinaryOp('+', exprs_prod(subs), c_ast.Constant('int', '1')),
                               self.sizes[0]
                               )
            )    # todo 0?

        return c_ast.Assignment('=', left, right)

    def __rand_init(self, depth: int) -> c_ast.Node:
        """
        todo
        :param depth:
        :return:
        """
        subs = self.__subs(depth)
        left = self.__array_ref(subs)

        right = \
            c_ast.Cast(
                self.dtype,
                c_ast.FuncCall(
                    c_ast.ID('rand'),
                    c_ast.ExprList([])
                )
            )

        return c_ast.Assignment('=', left, right)

    def __subs(self, depth):
        """
        todo
        :param depth:
        :return:
        """
        return [
            c_ast.ID(self.counter_prefix + str(i))
            for i in range(depth)
        ]
