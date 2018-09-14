from pycparser import c_generator
from code_transform_utils.code_transformer_ast import CodeTransformerAST
from code_transform_utils.code_transformer_str import CodeTransformerStr
from code_transform_utils.code_transform_utils import remove_comments


class CodeTransformer:
    """
    See docs/transform/code_transformer.md
    """
    # noinspection PyShadowingNames
    def __init__(self,
                 includes,
                 code,
                 papi_scope,
                 main_name='main',
                 rename_bounds=False,
                 add_pragma_unroll=False,
                 gen_mallocs=False,
                 modifiers_to_remove=None,
                 verbose=False,
                 ):

        if modifiers_to_remove is None:
            modifiers_to_remove = []

        if papi_scope in ['pragma', 'function']:
            self.papi_scope = papi_scope
        else:
            raise ValueError('Incorrect \'papi_scope\' value in \'add_papi\' - expected \'pragma\' or \'function\'')

        self.includes = includes
        self.code = code
        self.rename_bounds = rename_bounds
        self.add_pragma_unroll = add_pragma_unroll
        self.gen_mallocs = gen_mallocs
        self.main_name = main_name
        self.modifiers_to_remove = modifiers_to_remove
        self.verbose = verbose

        self.pp = None
        self.max_param = None
        self.max_arr_dim = None

    def transform(self, return_mode='all'):
        self.__run_preprocessing()
        self.__run_parser(return_mode)
        self.__run_str_transform()

        return self.code

    # PRIVATE MEMBERS

    def __run_preprocessing(self):
        self.code = remove_comments(self.code)

    def __run_parser(self, return_mode='all'):
        pp = CodeTransformerAST(self.code, self.verbose, not self.gen_mallocs, main_name=self.main_name)
        pp.single_to_compound()
        pp.remove_modifiers(self.modifiers_to_remove)
        pp.add_papi(self.papi_scope)

        if self.gen_mallocs:
            pp.analyse()

            self.max_param, self.max_arr_dim = pp.find_max_param()

            pp.arr_to_ptr_decl()
            pp.gen_mallocs()
            
            if not self.rename_bounds:
                pp.remove_bound_decls()

        if self.add_pragma_unroll:
            pp.add_pragma_unroll()

        if self.rename_bounds:
            pp.rename_bounds()

        generator = c_generator.CGenerator()
        self.code = generator.visit(pp.main if return_mode == 'main' else pp.ast)
        self.pp = pp

    def __run_str_transform(self):
        pt = CodeTransformerStr(self.includes, self.code)

        pt.add_includes()

        if self.add_pragma_unroll:
            pt.remove_pragma_semicolon()
            pt.add_pragma_macro()

        if self.gen_mallocs:
            pt.add_max_macro()

        self.code = pt.includes + pt.code
