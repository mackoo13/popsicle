import os
from pycparser import c_ast, c_generator
import numpy as np
from malloc_builder import MallocBuilder
from proc_code_transformer import ProcCodeTransformer
from proc_utils import exprs_sum, papi_instr, loop_func_params

out_dir = os.path.join(os.environ['KERNEL_PATH'], 'conv')


def for_loop(counter, bound, loop):
    init = c_ast.DeclList([c_ast.Decl(
        counter, [], [], [],
        c_ast.TypeDecl(counter.name, [], c_ast.ID('int')),
        c_ast.Constant('int', '1'), None
    )])
    cond = c_ast.BinaryOp('<', counter, c_ast.BinaryOp('-', c_ast.ID(bound), c_ast.Constant('int', '1')))
    nxt = c_ast.Assignment('++', counter, None)
    stmt = c_ast.Compound([loop])
    loop = c_ast.For(init, cond, nxt, stmt)

    return loop


def loop_func_def(body):
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
    def __init__(self, dims=2, reverse_loops_order=False):
        if dims < 1:
            raise ValueError

        self.dims = dims
        self.reverse_loops_order = reverse_loops_order
        self.bounds = ['PARAM_N_' + str(d) for d in range(dims)]
        self.name = 'A'
        self.dtype = 'double'
        self.code = None

    def generate(self):
        mb = MallocBuilder(self.name, self.dtype, self.bounds, initialiser='polybench')
        mallocs = c_ast.Compound(mb.alloc_and_init())
        papi_begin, papi_end = papi_instr()

        offsets = self.__conv_offsets()
        subs = [c_ast.ID('i_' + str(dim)) for dim in range(self.dims)]

        lvalue = self.__array_ref(subs)
        rvalue = exprs_sum([self.__array_ref(relative_subs(subs, o)) for o in offsets])
        loop = c_ast.Assignment('=', lvalue, rvalue)

        loop_counters = subs if self.reverse_loops_order else subs[::-1]
        loop_bounds = self.bounds if self.reverse_loops_order else self.bounds[::-1]    # todo check

        for counter, bound in zip(loop_counters, loop_bounds):
            loop = for_loop(counter, bound, loop)

        func_loop = loop_func_def(c_ast.Compound(mallocs.block_items + papi_begin + [loop] + papi_end))

        gen = c_generator.CGenerator()
        code = gen.visit(c_ast.FileAST([self.__array_decl(), func_loop]))

        pt = ProcCodeTransformer('', code)
        pt.add_includes(other_includes=['stdlib.h'])
        self.code = pt.includes + pt.code

        return self.code

    def save(self):
        if self.code is None:
            raise ValueError

        dir_name = 'd' + str(self.dims) + '_r' + ('1' if self.reverse_loops_order else '0')
        dir_path = os.path.join(out_dir, dir_name)
        file_name = dir_name + '.c'
        max_param_file_name = dir_name + '_max_param.txt'
        params_names_file_name = dir_name + '_params_names.txt'

        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        with open(os.path.join(dir_path, file_name), 'w') as fout:
            fout.write(self.code)
            print('Saved code to ' + file_name)

        with open(os.path.join(dir_path, max_param_file_name), 'w') as fout:
            fout.write(str(self.__max_param()))

        with open(os.path.join(dir_path, params_names_file_name), 'w') as fout:
            fout.write(','.join(self.bounds))

    def __array_decl(self):
        type_decl = c_ast.TypeDecl(self.name, [], c_ast.IdentifierType([self.dtype]))

        decl_node = type_decl
        for _ in range(self.dims):
            decl_node = c_ast.PtrDecl([], decl_node)

        return c_ast.Decl(self.name, [], [], [], decl_node, None, None)

    def __array_ref(self, subs):
        if len(subs) == 0:
            return c_ast.ID(self.name)
        else:
            sub = subs[-1]
            return c_ast.ArrayRef(self.__array_ref(subs[:-1]), sub)

    def __conv_offsets(self):
        mesh_args = [[-1, 0, 1]] * self.dims
        mesh = np.meshgrid(*mesh_args)
        return np.dstack(mesh).reshape(-1, self.dims)

    def __max_param(self):
        max_n_iters = 20000000000
        max_n_loads = 1000000000
        max_n_cells = 500000000
        n_arrays = 1    # todo

        return int(min([
            np.math.pow(max_n_iters, 1 / self.dims),
            np.math.pow(max_n_cells / n_arrays, 1 / self.dims),
            np.math.pow(max_n_loads, 1 / self.dims) / 3,
        ]))


def main():
    dimss = range(2, 5)
    revs = (True, False)

    for dims in dimss:
        for rev in revs:
            ccg = ConvCodeGenerator(dims=dims, reverse_loops_order=rev)
            ccg.generate()
            ccg.save()


if __name__ == "__main__":
    main()
