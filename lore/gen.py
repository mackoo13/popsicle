from pycparser import c_ast, c_generator
import numpy as np
from malloc_builder import MallocBuilder
from proc_utils import exprs_sum


def relative_subs(subs, offsets):
    def relative_sub(sub, offset):
        if offset == 0:
            return sub
        else:
            op = '+' if offset > 0 else '-'
            return c_ast.BinaryOp(op, sub, c_ast.Constant('int', abs(offset)))

    return [relative_sub(sub, offset) for sub, offset in zip(subs, offsets)]


class ConvCodeGenerator:
    def __init__(self, dims=2):
        self.dims = dims

    def array_ref(self, subs):
        if len(subs) == 0:
            return c_ast.ID('A')
        else:
            sub = subs[-1]
            return c_ast.ArrayRef(self.array_ref(subs[:-1]), sub)

    def conv_offsets(self):
        mesh_args = [[-1, 0, 1]] * self.dims
        mesh = np.meshgrid(*mesh_args)
        return np.dstack(mesh).reshape(-1, self.dims)

    def generate(self):
        mb = MallocBuilder('A', 'double', ['N'] * self.dims, initialiser='polybench')
        mallocs = mb.alloc_and_init()
        mallocs = c_ast.Compound(mallocs)

        offsets = self.conv_offsets()
        subs = [c_ast.ID('q') for _ in range(self.dims)]
        loop = exprs_sum([self.array_ref(relative_subs(subs, o)) for o in offsets])

        for dim in range(self.dims):
            i = 'i_' + str(dim)
            init = c_ast.DeclList([c_ast.Decl(
                c_ast.ID(i), [], [], [],
                c_ast.TypeDecl(i, [], c_ast.ID('int')),
                c_ast.Constant('int', '0'), ''
            )])
            cond = c_ast.BinaryOp('<', c_ast.ID(i), c_ast.ID('N'))
            nxt = c_ast.Assignment('++', c_ast.ID(i), None)
            stmt = c_ast.Compound([loop])
            loop = c_ast.For(init, cond, nxt, stmt)

        gen = c_generator.CGenerator()
        code = gen.visit(c_ast.FileAST([mallocs, loop]))

        return code


def main():
    ccg = ConvCodeGenerator()
    code = ccg.generate()

    print(code)


if __name__ == "__main__":
    main()
