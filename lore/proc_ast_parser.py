from pycparser import c_ast, c_parser

from malloc_builder import MallocBuilder
from proc_utils import remove_non_extreme_numbers, estimate, \
    ArrayRefVisitor, ForVisitor, AssignmentVisitor, PtrDeclVisitor, StructVisitor, \
    ArrayDeclVisitor, VarTypeVisitor, ForPragmaUnrollVisitor, DeclRemoveModifiersVisitor, \
    FuncDefFindVisitor, CompoundInsertNextToVisitor, ForDepthCounter, SingleToCompoundVisitor, build_decl, \
    ParseException, ReturnIntVisitor, ArrayDeclToPtrVisitor
import math


class ProcASTParser:
    def __init__(self, code, verbose=False, allow_struct=False, main_name='main'):
        self.maxs = {}
        self.refs = {}
        self.dims = {}
        self.dtypes = {}
        self.bounds = set()
        self.verbose = verbose

        astparser = c_parser.CParser()
        self.ast = astparser.parse(code)

        ffv = FuncDefFindVisitor(main_name)
        ffv.visit(self.ast)
        self.main = ffv.res

        if verbose:
            self.ast.show()

        if not allow_struct:
            sv = StructVisitor()
            sv.visit(self.ast)
            if sv.contains_struct:
                raise ParseException('Skipping - file contains struct')

    def add_bounds_init(self):
        """
        Inserts a fragment initializing program parameters into the code.
        The actual values should be injected at compilation time (-D option in gcc)
        """
        inits = [c_ast.Assignment('=', c_ast.ID(n), c_ast.ID('PARAM_' + n.upper())) for n in self.bounds]
        self.main.body.block_items[0:0] = inits

    def add_papi(self):
        """
        todo
        """
        body = self.main.body

        self.change_loop_signature()

        if type(body) is c_ast.Compound:
            papi_start = c_ast.FuncCall(c_ast.ID('PAPI_start'), c_ast.ParamList([c_ast.ID('set')]))
            papi_stop = c_ast.FuncCall(c_ast.ID('PAPI_stop'),
                                       c_ast.ParamList([c_ast.ID('set'), c_ast.ID('values')]))
            exec_start = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_start]))
            exec_stop = c_ast.FuncCall(c_ast.ID('exec'), c_ast.ParamList([papi_stop]))

            clock = c_ast.FuncCall(c_ast.ID('clock'), c_ast.ParamList([]))
            begin_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('begin')), clock)
            end_clock = c_ast.Assignment('=', c_ast.UnaryOp('*', c_ast.ID('end')), clock)

            CompoundInsertNextToVisitor('before', 'Pragma', [exec_start, begin_clock],
                                        properties={'string': 'scop'}).visit(body)
            CompoundInsertNextToVisitor('after', 'Pragma', [end_clock, exec_stop],
                                        properties={'string': 'endscop'}).visit(body)

    def add_pragma_unroll(self):
        """
        todo
        """
        res = [0]
        ForPragmaUnrollVisitor(1, res).visit(self.ast)
        if res[0] == 1:
            pragma = c_ast.FuncCall(c_ast.ID('PRAGMA'), c_ast.ExprList([c_ast.ID('PRAGMA_UNROLL')]))
            CompoundInsertNextToVisitor('before', 'For', [pragma]).visit(self.ast)

    def analyse(self):
        """
        Extract useful information from AST tree
        """

        ForVisitor(self.maxs, self.bounds).visit(self.ast)
        AssignmentVisitor(self.refs, self.maxs).visit(self.ast)

        for var in self.maxs:
            self.maxs[var] = set(remove_non_extreme_numbers(self.maxs[var]))

        ArrayRefVisitor(self.refs, self.maxs).visit(self.ast)

        for arr in self.refs:
            new_refs = []
            for ref in self.refs[arr]:
                new_refs.append(estimate(ref, self.maxs, arr))
            self.refs[arr] = new_refs

        PtrDeclVisitor(self.dtypes).visit(self.ast)
        ArrayDeclVisitor(self.dtypes, self.dims).visit(self.ast)
        VarTypeVisitor(self.dtypes).visit(self.ast)

        self.bounds.difference_update(self.refs.keys())

        if self.verbose:
            self.print_debug_info()

    def arr_to_ptr_decl(self):
        ArrayDeclToPtrVisitor(self.dims).visit(self.ast)

    def change_loop_signature(self):
        decl = self.main.decl

        if type(decl.type) is c_ast.FuncDecl:
            decl.type.args = c_ast.ParamList([
                build_decl('set', 'int'),
                build_decl('values', 'long_long*'),
                build_decl('begin', 'clock_t*'),
                build_decl('end', 'clock_t*'),
            ])
            decl.type.type.declname = 'loop'

    def for_depth(self):
        """
        Finds the maximal depth of nested for loops.
        :return: Max depth
        """
        res = [0]
        ForDepthCounter(1, res).visit(self.ast)
        return res[0]

    def find_max_param(self):
        """
        Attempts to find the maximal value of program parameters. The upper bound is either imposed by limited memory
        (based on arrays dimensionality and their number) or loop count (based on for loop depth)

        if multiple parameters are present, all are assumed to be equal.
        :return: The maximal parameter
        """
        max_arr_dim = max([len(refs) for refs in self.refs.values()])
        arr_count = len(self.refs)
        loop_depth = self.for_depth()

        max_param_arr = math.pow(50000000 / arr_count, 1 / max_arr_dim)
        max_param_loop = math.pow(5000000000, 1 / loop_depth)
        max_param = min(max_param_arr, max_param_loop)

        return max_param, max_arr_dim

    def gen_mallocs(self):
        for arr in self.refs:
            ref = self.refs[arr]

            if arr in self.dtypes:
                mb = MallocBuilder(arr, self.dtypes[arr], ref)
                self.main.body.block_items[0:0] = mb.alloc_and_init()

    def main_to_loop(self):
        """
        todo
        """
        decl = self.main.decl
        body = self.main.body

        if decl.name == 'main':
            decl.name = 'loop'

            self.change_loop_signature()

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
                CompoundInsertNextToVisitor('before', 'Return', [end_clock, exec_stop]).visit(body)

    def print_debug_info(self):
        print('maxs: ', self.maxs)
        print('bounds: ', self.bounds)
        print('refs: ', self.refs)
        print('dtypes: ', self.dtypes)
        print('dims: ', self.dims)

    def remove_modifiers(self, modifiers_to_remove):
        DeclRemoveModifiersVisitor(modifiers_to_remove).visit(self.ast)

    def return_int(self):
        ReturnIntVisitor().visit(self.main)

    def single_to_compound(self):
        SingleToCompoundVisitor().visit(self.main)
