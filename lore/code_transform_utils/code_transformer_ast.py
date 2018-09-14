from typing import Iterable

from pycparser import c_ast, c_parser

from code_transform_utils.expr_estimator import ExprEstimator, remove_non_extreme_numbers
from code_transform_utils.malloc_builder import MallocBuilder
from code_transform_utils.code_transform_utils import ArrayRefVisitor, ForVisitor, AssignmentVisitor, PtrDeclVisitor, \
    StructVisitor, ArrayDeclVisitor, VarTypeVisitor, ForPragmaUnrollVisitor, DeclRemoveModifiersVisitor, \
    FuncDefFindVisitor, CompoundInsertNextToVisitor, ForDepthCounter, SingleToCompoundVisitor, \
    ParseException, ReturnIntVisitor, ArrayDeclToPtrVisitor, papi_instr, pragma_unroll, loop_func_params, \
    RemoveBoundDeclsVisitor
import math


class CodeTransformerAST:
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
        if ffv.res is not None:
            self.main = ffv.res
        else:
            raise ValueError('CodeTransformer: function \'' + main_name + '\' not found')

        if verbose:
            self.ast.show()

        if not allow_struct:
            sv = StructVisitor()
            sv.visit(self.ast)
            if sv.contains_struct:
                raise ParseException('Skipping - file contains struct')

    def rename_bounds(self):
        """
        Inserts a code fragment initializing program parameters.
        The actual values should be injected at compilation time (-D option in gcc)
        """
        inits = [c_ast.Assignment('=', c_ast.ID(n), c_ast.ID('PARAM_' + n.upper()))
                 for n in self.bounds]
        self.main.body.block_items[0:0] = inits

    def add_papi(self, scope):
        """
        Inserts code responsible for starting PAPI and making PAPI and execution time measurements
        """
        body = self.main.body
        [exec_start, begin_clock], [end_clock, exec_stop] = papi_instr()

        if type(body) is not c_ast.Compound:
            return

        if scope == 'pragma':
            CompoundInsertNextToVisitor('before', 'Pragma', [exec_start, begin_clock],
                                        properties={'string': 'scop'}).visit(body)
            CompoundInsertNextToVisitor('after', 'Pragma', [end_clock, exec_stop],
                                        properties={'string': 'endscop'}).visit(body)
        elif scope == 'function':
            body.block_items.insert(0, exec_start)
            body.block_items.insert(1, begin_clock)
            CompoundInsertNextToVisitor('before', 'Return', [end_clock, exec_stop]).visit(body)
        else:
            raise ValueError(
                'CodeTransformer: incorrect \'scope\' value in \'add_papi\' - expected \'pragma\' or \'function\'')

        self.__change_loop_signature()

    def add_pragma_unroll(self):
        """
        Inserts #pragma statement defining the type of unrolling next to every innermost loop
        """
        fpuv = ForPragmaUnrollVisitor()
        fpuv.visit(self.ast)

        if fpuv.depth == 1:
            CompoundInsertNextToVisitor('before', 'For', [pragma_unroll()]).visit(self.ast)

    def analyse(self):
        """
        Analyses the code and populates following variables:
            bounds
            maxs
            refs
        """
        ForVisitor(self.maxs, self.bounds).visit(self.ast)
        AssignmentVisitor(self.refs, self.maxs).visit(self.ast)

        for var in self.maxs:
            self.maxs[var] = set(remove_non_extreme_numbers(self.maxs[var]))

        ArrayRefVisitor(self.refs, self.maxs).visit(self.ast)

        for arr in self.refs:
            new_refs = []
            for ref in self.refs[arr]:
                new_refs.append(ExprEstimator(self.maxs, arr).estimate(ref))
            self.refs[arr] = new_refs

        PtrDeclVisitor(self.dtypes).visit(self.ast)
        ArrayDeclVisitor(self.dtypes, self.dims).visit(self.ast)
        VarTypeVisitor(self.dtypes).visit(self.ast)

        self.bounds.difference_update(self.refs.keys())

        if self.verbose:
            self.print_debug_info()

    def arr_to_ptr_decl(self):
        """
        Converts all arrays declared like 'int A[42]' to 'int* A'
        """
        ArrayDeclToPtrVisitor(self.dims).visit(self.ast)

    def find_max_param(self):
        """
        Attempts to find the maximal value of program parameters. The upper bound is either imposed by limited memory
        (based on arrays dimensionality and their number) or loop count (based on for loop depth)

        if multiple parameters are present, all are assumed to be equal.
        :return: The maximal parameter
        """
        if len(self.refs) == 0:
            raise ParseException('No refs found - cannot determine max_arr_dim')

        max_arr_dim = max([len(refs) for refs in self.refs.values()])
        arr_count = len(self.refs)
        loop_depth = self.__for_depth()

        max_param_arr = math.pow(50000000 / arr_count, 1 / max_arr_dim)
        max_param_loop = math.pow(5000000000, 1 / loop_depth)
        max_param = int(min(max_param_arr, max_param_loop))

        return max_param, max_arr_dim

    def gen_mallocs(self):
        """
        Generates code responsible for array allocation and initialisation
        """
        for arr in self.refs:
            ref = self.refs[arr]

            for dim_size in ref:
                if len(dim_size) == 0:
                    raise ParseException('Unknown dimensions of array ' + arr)

            if arr in self.dtypes:
                mb = MallocBuilder(arr, self.dtypes[arr], ref)
                self.main.body.block_items[0:0] = mb.generate()

    def print_debug_info(self):
        print('maxs: ', self.maxs)
        print('bounds: ', self.bounds)
        print('refs: ', self.refs)
        print('dtypes: ', self.dtypes)
        print('dims: ', self.dims)

    def remove_bound_decls(self):
        """
        Removes all declarations of variables which will be provided on compilation time.
        """
        RemoveBoundDeclsVisitor(self.bounds).visit(self.ast)

    def remove_modifiers(self, modifiers_to_remove: Iterable[str]):
        """
        Removes all indicated modifiers from variable declarations (for example 'extern')
        :param modifiers_to_remove:
        """
        DeclRemoveModifiersVisitor(modifiers_to_remove).visit(self.ast)

    def single_to_compound(self):
        """
        Transforms single expressions to compounds where possible to facilitate parsing
        """
        if self.main is None:
            raise ValueError('CodeTransformer: single_to_compound() called with self.main=None')

        SingleToCompoundVisitor().visit(self.main)

    # PRIVATE MEMBERS

    def __change_loop_signature(self):
        """
        Changes the self.main function signature to:
            int loop(int set, long_long* values, clock_t* begin, clock_t* end)
        """
        decl = self.main.decl
        decl.name = 'loop'

        func_decl = decl.type
        if type(func_decl) is c_ast.FuncDecl:
            func_decl.args = loop_func_params()
            func_decl.type.declname = 'loop'
            func_decl.type.type = c_ast.IdentifierType(['int'])

        self.__return_int()

    def __for_depth(self):
        """
        Finds the maximal depth of nested for loops.
        :return: Max depth
        """
        fdc = ForDepthCounter(0)
        fdc.visit(self.ast)
        return fdc.result

    def __return_int(self):
        """
        Changes every 'return;' to 'return 0;'
        """
        ReturnIntVisitor().visit(self.main)
