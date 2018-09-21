import os
import shutil
from typing import List
from pycparser import c_ast, c_generator
import numpy as np
from popsicle.code_transform_utils.malloc_builder import MallocBuilder
from popsicle.code_transform_utils.code_transformer_str import CodeTransformerStr
from popsicle.code_transform_utils.code_transform_utils import exprs_sum, papi_instr, loop_func_params

if 'KERNEL_PATH' not in os.environ:
    raise EnvironmentError

out_dir = os.path.join(os.environ['KERNEL_PATH'], 'conv')


def for_loop(counter, bound, loop):
    init = c_ast.DeclList([c_ast.Decl(
        counter, [], [], [],
        c_ast.TypeDecl(counter.name, [], c_ast.IdentifierType(['int'])),
        c_ast.Constant('int', '1'), None
    )])
    cond = c_ast.BinaryOp('<', counter, c_ast.BinaryOp('-', c_ast.ID(bound), c_ast.Constant('int', '1')))
    nxt = c_ast.Assignment('++', counter, None)
    stmt = c_ast.Compound([loop])
    loop = c_ast.For(init, cond, nxt, stmt)

    return loop


def loop_func_def(body) -> c_ast.Node:
    func_decl = c_ast.FuncDecl(
        loop_func_params(),
        c_ast.TypeDecl('loop', [], c_ast.IdentifierType(['int']))
    )
    func_loop = c_ast.FuncDef(
        c_ast.Decl('loop', [], [], [], func_decl, None, None),
        [],
        body
    )
    return func_loop


def relative_subs(subs, offsets):
    def relative_sub(sub, offset):
        if offset == 0:
            return sub
        else:
            op = '+' if offset > 0 else '-'
            return c_ast.BinaryOp(op, sub, c_ast.Constant('int', abs(offset)))

    return [relative_sub(sub, offset) for sub, offset in zip(subs, offsets)]


class ConvCodeGenerator:
    def __init__(self, dims=2, reverse_loops_order=False, n_arrays=1):
        if dims < 1:
            raise ValueError('ConvCodeGenerator: expected dims >= 2.')

        self.offsets = [-1, 1]
        self.dims = dims
        self.reverse_loops_order = reverse_loops_order
        self.n_arrays = min([n_arrays, np.math.floor(np.math.pow(len(self.offsets), dims))])
        self.bounds = ['PARAM_N_' + str(d) for d in range(dims)]
        self.names = ['A_' + str(a) for a in range(n_arrays)]
        self.dtype = 'double'
        self.code = None

    def generate(self):
        mallocs = []
        for name in self.names:
            mb = MallocBuilder(name, self.dtype, self.bounds, initialiser='polybench')
            mallocs.extend(mb.generate())
        mallocs = c_ast.Compound(mallocs)
        papi_begin, papi_end = papi_instr()

        offsets = self.__conv_offsets()
        subs = [c_ast.ID('i_' + str(dim)) for dim in range(self.dims)]

        lvalue = self.__array_ref(self.names[0], subs)
        rvalue = exprs_sum(
            [self.__array_ref(
                self.names[i if i < self.n_arrays else 0],
                relative_subs(subs, o)
            ) for i, o in enumerate(offsets)])
        loop = c_ast.Assignment('=', lvalue, rvalue)

        loop_counters = subs if self.reverse_loops_order else subs[::-1]
        loop_bounds = self.bounds if self.reverse_loops_order else self.bounds[::-1]

        for counter, bound in zip(loop_counters, loop_bounds):
            loop = for_loop(counter, bound, loop)

        func_loop = loop_func_def(c_ast.Compound(mallocs.block_items + papi_begin + [loop] + papi_end))

        gen = c_generator.CGenerator()
        code = gen.visit(c_ast.FileAST(self.__array_decls() + [func_loop]))

        pt = CodeTransformerStr('', code)
        pt.add_includes(other_includes=['stdlib.h'])
        self.code = pt.includes + pt.code

        return self.code

    def save(self):
        if self.code is None:
            raise ValueError('ConvCodeGenerator: save() called with self.code=None')

        dir_name = 'd' + str(self.dims) + \
                   '_r' + ('1' if self.reverse_loops_order else '0') + \
                   '_a' + str(self.n_arrays)
        dir_path = os.path.join(out_dir, dir_name)
        file_name = dir_name + '.c'
        max_param_file_name = dir_name + '_max_param.txt'
        params_names_file_name = dir_name + '_params_names.txt'

        shutil.rmtree(dir_path)

        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        with open(os.path.join(dir_path, file_name), 'w') as fout:
            fout.write(self.code)
            print('Saved code to ' + file_name)

        with open(os.path.join(dir_path, max_param_file_name), 'w') as fout:
            fout.write(str(self.__max_param()))

        with open(os.path.join(dir_path, params_names_file_name), 'w') as fout:
            fout.write(','.join(self.bounds))

    # PRIVATE MEMBERS

    def __array_decl(self, name: str) -> c_ast.Node:
        type_decl = c_ast.TypeDecl(name, [], c_ast.IdentifierType([self.dtype]))

        decl_node = type_decl
        for _ in range(self.dims):
            decl_node = c_ast.PtrDecl([], decl_node)

        return c_ast.Decl(name, [], [], [], decl_node, None, None)

    def __array_decls(self) -> List[c_ast.Node]:
        return [self.__array_decl(name) for name in self.names]

    def __array_ref(self, name, subs):
        if len(subs) == 0:
            return c_ast.ID(name)
        else:
            sub = subs[-1]
            return c_ast.ArrayRef(self.__array_ref(name, subs[:-1]), sub)

    def __conv_offsets(self):
        mesh_args = [self.offsets] * self.dims
        mesh = np.meshgrid(*mesh_args)
        return np.dstack(mesh).reshape(-1, self.dims)

    def __max_param(self):
        max_n_iters = 20000000000
        max_n_loads = 1000000000
        max_n_cells = 50000000

        return int(min([
            np.math.pow(max_n_iters, 1 / self.dims),                            # N^dims <= n_iters
            np.math.pow(max_n_cells / self.n_arrays, 1 / self.dims),            # n_arrays * N^dims <= n_cells
            np.math.pow(max_n_loads, 1 / self.dims) / len(self.offsets),        # (3N)^dims <= n_loads
        ]))


def main():
    dimss = range(2, 5)
    revs = (True, False)
    n_arrayss = [1, 2, 3, 5, 10]

    for dims in dimss:
        for rev in revs:
            for n_arrays in n_arrayss:
                ccg = ConvCodeGenerator(dims=dims, reverse_loops_order=rev, n_arrays=n_arrays)
                ccg.generate()
                ccg.save()


if __name__ == "__main__":
    main()
