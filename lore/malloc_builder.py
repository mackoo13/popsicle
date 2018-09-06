from pycparser import c_ast
from proc_utils import remove_non_extreme_numbers, exprs_prod


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
    if type(s) is str:
        return c_ast.ID(s)

    s = remove_non_extreme_numbers(s, leave_min=False)
    s = [c_ast.ID(e) for e in s]

    return max_set_recur(s)


def max_set_recur(s):
    if len(s) == 0:
        return None
    if len(s) == 1:
        return s[0]
    else:
        half = int(len(s) / 2)
        a = max_set_recur(s[:half])
        b = max_set_recur(s[half:])
        return c_ast.FuncCall(c_ast.ID('MAX'), c_ast.ExprList([a, b]))


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
        self.initialiser = self.polybench_init if initialiser == 'polybench' else self.rand_init
        self.counter_prefix = 'i_' if not name.startswith('i_') else 'i' + name

    def alloc_and_init(self):
        return [
            self.malloc_assign(0),
            self.for_loop(0)
        ]

    def malloc(self, depth):
        size_expr = c_ast.BinaryOp('+', self.sizes[depth], c_ast.ID('2'))
        sizeof = c_ast.FuncCall(c_ast.ID('sizeof'),
                                c_ast.ExprList([c_ast.ID(self.dtype.name + '*' * (len(self.sizes) - depth - 1))]))
        arg = c_ast.BinaryOp('*', size_expr, sizeof)
        return c_ast.FuncCall(c_ast.ID('malloc'), c_ast.ExprList([arg]))

    def malloc_assign(self, depth):
        subs = [c_ast.ID(self.counter_prefix + str(i)) for i in range(depth)]
        return c_ast.Assignment('=', self.array_ref(subs), self.malloc(depth))

    def polybench_init(self, depth):
        subs = [c_ast.ID(self.counter_prefix + str(i)) for i in range(depth)]
        left = self.array_ref(subs)
        right = c_ast.Cast(self.dtype, c_ast.BinaryOp('/', exprs_prod(subs), self.sizes[0]))    # todo 0?
        return c_ast.Assignment('=', left, right)

    def rand_init(self, depth):
        subs = [c_ast.ID(self.counter_prefix + str(i)) for i in range(depth)]
        left = self.array_ref(subs)
        right = c_ast.Cast(self.dtype, c_ast.FuncCall(c_ast.ID('rand'), c_ast.ExprList([])))
        return c_ast.Assignment('=', left, right)

    def array_ref(self, subs):
        if len(subs) == 0:
            return c_ast.ID(self.name)
        else:
            sub = subs[-1]  # todo not tested
            return c_ast.ArrayRef(self.array_ref(subs[:-1]), sub)

    def for_loop(self, depth):
        i = self.counter_prefix + str(depth)
        init = c_ast.DeclList([c_ast.Decl(
            c_ast.ID(i), [], [], [],
            c_ast.TypeDecl(i, [], c_ast.ID('int')),
            c_ast.Constant('int', '0'), ''
        )])
        cond = c_ast.BinaryOp('<', c_ast.ID(i), self.sizes[depth])
        nxt = c_ast.Assignment('++', c_ast.ID(i), None)
        stmt = c_ast.Compound([])

        if depth < len(self.sizes) - 1:
            stmt.block_items = [self.malloc_assign(depth + 1), self.for_loop(depth + 1)]
        else:
            stmt.block_items = [self.initialiser(depth + 1)]

        return c_ast.For(init, cond, nxt, stmt)
