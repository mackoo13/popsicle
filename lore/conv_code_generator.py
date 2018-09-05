from pycparser import c_ast, c_generator
import numpy as np
from malloc_builder import MallocBuilder
from proc_utils import exprs_sum, papi_instr, build_decl


def relative_subs(subs, offsets):
    def relative_sub(sub, offset):
        if offset == 0:
            return sub
        else:
            op = '+' if offset > 0 else '-'
            return c_ast.BinaryOp(op, sub, c_ast.Constant('int', abs(offset)))

    return [relative_sub(sub, offset) for sub, offset in zip(subs, offsets)]


class ConvCodeGenerator:
    def __init__(self, dims=2, reverse_loops_order=False):
        self.dims = dims
        self.reverse_loops_order = reverse_loops_order
        self.bound = 'N'
        self.name = 'A'

    def array_ref(self, subs):
        if len(subs) == 0:
            return c_ast.ID(self.name)
        else:
            sub = subs[-1]
            return c_ast.ArrayRef(self.array_ref(subs[:-1]), sub)

    def conv_offsets(self):
        mesh_args = [[-1, 0, 1]] * self.dims
        mesh = np.meshgrid(*mesh_args)
        return np.dstack(mesh).reshape(-1, self.dims)

    def generate(self):
        mb = MallocBuilder(self.name, 'double', [self.bound] * self.dims, initialiser='polybench')
        mallocs = mb.alloc_and_init()
        mallocs = c_ast.Compound(mallocs)

        papi_begin, papi_end = papi_instr()

        offsets = self.conv_offsets()
        subs = [c_ast.ID('i_' + str(dim)) for dim in range(self.dims)]

        lvalue = self.array_ref(subs)
        rvalue = exprs_sum([self.array_ref(relative_subs(subs, o)) for o in offsets])
        loop = c_ast.Assignment('=', lvalue, rvalue)

        loop_counters = subs if self.reverse_loops_order else subs[::-1]
        for counter in loop_counters:
            init = c_ast.DeclList([c_ast.Decl(
                counter, [], [], [],
                c_ast.TypeDecl(counter.name, [], c_ast.ID('int')),
                c_ast.Constant('int', 1), ''
            )])
            cond = c_ast.BinaryOp('<', counter, c_ast.BinaryOp('-', c_ast.ID(self.bound), c_ast.Constant('int', 1)))
            nxt = c_ast.Assignment('++', counter, None)
            stmt = c_ast.Compound([loop])
            loop = c_ast.For(init, cond, nxt, stmt)

        func_decl = c_ast.FuncDecl(c_ast.ParamList([
            build_decl('set', 'int'),
            build_decl('values', 'long_long*'),
            build_decl('begin', 'clock_t*'),
            build_decl('end', 'clock_t*'),
        ]), c_ast.TypeDecl('loop', [], c_ast.IdentifierType(['int'])))
        func_loop = c_ast.FuncDef(
            c_ast.Decl('loop', [], [], [], func_decl, None, None),
            [],
            c_ast.Compound(mallocs.block_items + papi_begin + [loop] + papi_end)
        )

        gen = c_generator.CGenerator()
        code = gen.visit(c_ast.FileAST([func_loop]))

        return code


def main():
    ccg = ConvCodeGenerator(dims=3)
    code = ccg.generate()

    print(code)


if __name__ == "__main__":
    main()
