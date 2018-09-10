from pycparser import c_generator
from code_transform_utils.code_transformer_ast import CodeTransformerAST
from code_transform_utils.code_transformer_str import CodeTransformerStr
from code_transform_utils.code_transform_utils import remove_comments, remove_inline


class CodeTransformer:
    # noinspection PyShadowingNames
    def __init__(self,
                 includes,
                 code,
                 papi_scope,
                 main_name='main',
                 add_bounds_init=False,
                 add_pragma_unroll=False,
                 allow_struct=False,
                 arr_to_ptr_decl=False,
                 gen_mallocs=False,
                 modifiers_to_remove=None,
                 remove_comments=False,
                 remove_inline=False,
                 return_only_main=False,
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
        self.add_bounds_init = add_bounds_init
        self.add_pragma_unroll = add_pragma_unroll
        self.allow_struct = allow_struct
        self.arr_to_ptr_decl = arr_to_ptr_decl
        self.gen_mallocs = gen_mallocs
        self.main_name = main_name
        self.modifiers_to_remove = modifiers_to_remove
        self.remove_comments = remove_comments
        self.remove_inline = remove_inline
        self.return_only_main = return_only_main
        self.verbose = verbose

        self.pp = None
        self.max_param = None
        self.max_arr_dim = None

    def transform(self):
        self.__run_preprocessing()
        self.__run_parser()
        self.__run_str_transform()

        return self.code

    def __run_preprocessing(self):
        if self.remove_comments:
            self.code = remove_comments(self.code)

        if self.remove_inline:
            self.code = remove_inline(self.code)

    def __run_parser(self):
        pp = CodeTransformerAST(self.code, self.verbose, self.allow_struct, main_name=self.main_name)
        pp.single_to_compound()
        pp.remove_modifiers(self.modifiers_to_remove)
        pp.add_papi(self.papi_scope)

        if self.gen_mallocs:
            pp.analyse()
            pp.gen_mallocs()
            self.max_param, self.max_arr_dim = pp.find_max_param()

        if self.add_pragma_unroll:
            pp.add_pragma_unroll()

        if self.add_bounds_init:
            pp.add_bounds_init()

        if self.arr_to_ptr_decl:
            pp.arr_to_ptr_decl()

        generator = c_generator.CGenerator()
        self.code = generator.visit(pp.main if self.return_only_main else pp.ast)
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
