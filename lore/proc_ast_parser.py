from proc_utils import remove_non_extreme_numbers, estimate, \
    ArrayRefVisitor, ForVisitor, AssignmentVisitor, PtrDeclVisitor, StructVisitor, \
    ArrayDeclVisitor, TypeDeclVisitor, ForPragmaUnrollVisitor, CompoundVisitor, DeclVisitor, \
    FuncFinderVisitor, main_to_loop


class ProcASTParser:
    def __init__(self, ast, verbose=False, allow_struct=False, main_name='main'):
        self.maxs = {}
        self.refs = {}
        self.dims = {}
        self.dtypes = {}
        self.bounds = set()
        self.ast = ast
        self.verbose = verbose

        ffv = FuncFinderVisitor(main_name)
        ffv.visit(ast)
        self.main = ffv.main

        if verbose:
            ast.show()

        if not allow_struct:
            sv = StructVisitor()
            sv.visit(ast)
            if sv.contains_struct:
                print('\tSkipping - file contains struct')

    def add_pragma_unroll(self):
        """
        todo
        """
        res = [0]
        ForPragmaUnrollVisitor(1, res).visit(self.ast)
        if res[0] == 1:
            CompoundVisitor().visit(self.ast)

    def analyze(self, ast, verbose=False):
        """
        Extract useful information from AST tree
        :param ast: AST tree object
        :param verbose: If True, the output will be printed
        :return:
            res (string) - malloc instructions and array initialization)
            bounds () -
            refs () -
            dtypes (map: array_name: str -> data type: str)
            dims (map: array_name: str -> dimensions: int[])
        """

        ForVisitor(self.maxs, self.bounds).visit(ast)
        AssignmentVisitor(self.refs, self.maxs).visit(ast)

        for var in self.maxs:
            self.maxs[var] = set(remove_non_extreme_numbers(self.maxs[var]))

        ArrayRefVisitor(self.refs, self.maxs).visit(ast)

        deps = {}
        for arr in self.refs:
            self.refs[arr] = [set([estimate(r, self.maxs, arr, deps) for r in ref]) for ref in self.refs[arr]]

        PtrDeclVisitor(self.dtypes).visit(ast)
        ArrayDeclVisitor(self.dtypes, self.dims).visit(ast)
        TypeDeclVisitor(self.dtypes).visit(ast)

        self.bounds.difference_update(self.refs.keys())

        if verbose:
            self.print_debug_info()

    def main_to_loop(self):
        main_to_loop(self.main)

    def print_debug_info(self):
        print('maxs: ', self.maxs)
        print('bounds: ', self.bounds)
        print('refs: ', self.refs)
        print('dtypes: ', self.dtypes)
        print('dims: ', self.dims)

    def remove_extern(self):
        DeclVisitor().visit(self.ast)
