from pycparser import c_ast, c_parser
from proc_utils import remove_non_extreme_numbers, estimate, \
    ArrayRefVisitor, ForVisitor, AssignmentVisitor, PtrDeclVisitor, StructVisitor, \
    ArrayDeclVisitor, TypeDeclVisitor, ForPragmaUnrollVisitor, DeclVisitor, \
    FuncFinderVisitor, main_to_loop, CompoundInsertBeforeVisitor, ForDepthCounter
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

        ffv = FuncFinderVisitor(main_name)
        ffv.visit(self.ast)
        self.main = ffv.main

        if verbose:
            self.ast.show()

        if not allow_struct:
            sv = StructVisitor()
            sv.visit(self.ast)
            if sv.contains_struct:
                print('\tSkipping - file contains struct')

    def add_pragma_unroll(self):
        """
        todo
        """
        res = [0]
        ForPragmaUnrollVisitor(1, res).visit(self.ast)
        if res[0] == 1:
            pragma = c_ast.FuncCall(c_ast.ID('PRAGMA'), c_ast.ExprList([c_ast.ID('PRAGMA_UNROLL')]))
            CompoundInsertBeforeVisitor('For', [pragma]).visit(self.ast)

    def analyse(self):
        """
        Extract useful information from AST tree
        :return:
            res (string) - malloc instructions and array initialization)
            bounds () -
            refs () -
            dtypes (map: array_name: str -> data type: str)
            dims (map: array_name: str -> dimensions: int[])
        """

        ForVisitor(self.maxs, self.bounds).visit(self.ast)
        AssignmentVisitor(self.refs, self.maxs).visit(self.ast)

        for var in self.maxs:
            self.maxs[var] = set(remove_non_extreme_numbers(self.maxs[var]))

        ArrayRefVisitor(self.refs, self.maxs).visit(self.ast)

        deps = {}
        for arr in self.refs:
            self.refs[arr] = [set([estimate(r, self.maxs, arr, deps) for r in ref]) for ref in self.refs[arr]]

        PtrDeclVisitor(self.dtypes).visit(self.ast)
        ArrayDeclVisitor(self.dtypes, self.dims).visit(self.ast)
        TypeDeclVisitor(self.dtypes).visit(self.ast)

        self.bounds.difference_update(self.refs.keys())

        if self.verbose:
            self.print_debug_info()

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

    def main_to_loop(self):
        main_to_loop(self.main)

    def print_debug_info(self):
        print('maxs: ', self.maxs)
        print('bounds: ', self.bounds)
        print('refs: ', self.refs)
        print('dtypes: ', self.dtypes)
        print('dims: ', self.dims)

    def remove_modifiers(self, modifiers_to_remove):
        DeclVisitor(modifiers_to_remove).visit(self.ast)
