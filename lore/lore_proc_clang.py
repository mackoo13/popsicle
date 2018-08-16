from __future__ import print_function

from pycparser import c_parser, c_generator
import re
import os
import argparse

from lore_proc_utils import add_includes, add_papi, split_code, sub_loop_header, del_extern_restrict, gen_mallocs, \
    arr_to_ptr_decl, add_mallocs, find_max_param
from lore_parser import analyze, ParseException
from lore_parser_clang import add_pragma_unroll


def add_pragma_macro(includes):
    """
    :param includes: C code section containing #include's (as string)
    :return: Transformed code
    """
    includes += '#define PRAGMA(p) _Pragma(p)\n'
    return includes


def remove_pragma_semicolon(code):
    """
    Removes the semicolon after PRAGMA macro (added unintentionally by pycparser)
    :param code: C code
    :return: Transformed code
    """
    code = re.sub(r'(PRAGMA\(.*\));', r'\1', code)
    return code


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
        parser.add_argument("file_path", help="File path")
        parser.add_argument("proc_path", help="Proc path")
        args = parser.parse_args()
        verbose = args.verbose
        file_path = args.file_path
        file_name = file_path.split('/')[-1]
        file_name = file_name.split('.')[0]
        proc_path = args.proc_path

        out_dir = proc_path + file_name

        with open(file_path, 'r') as fin:
            code = fin.read()
            includes, code = split_code(code)

            # if lore_parser_clang.contains_struct(code):
            #     pass
            #     raise lore_parser_clang.ParseException('Code contains struct declaration.')

            parser = c_parser.CParser()
            ast = parser.parse(code)

            if verbose:
                ast.show()

            add_pragma_unroll(ast)
            generator = c_generator.CGenerator()
            code = generator.visit(ast)
            code = remove_pragma_semicolon(code)

            includes = add_includes(includes)
            includes = add_pragma_macro(includes)

            bounds, refs, dtypes, dims = analyze(ast, verbose)
            mallocs = gen_mallocs(bounds, refs, dtypes)

            code = del_extern_restrict(code)
            code = arr_to_ptr_decl(code, dtypes, dims)
            code = add_papi(code)
            code = add_mallocs(code, mallocs)
            code = sub_loop_header(code)
            code = includes + code

            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

            if len(refs) == 0:
                raise ParseException('No refs found - cannot determine max_arr_dim')

            with open(out_dir + '/' + file_name + '.c', 'w') as fout:
                fout.write(code)

            max_param = find_max_param(refs, ast, verbose)
            with open(out_dir + '/' + file_name + '_max_param.txt', 'w') as fout:
                fout.write(str(int(max_param)))

            with open(out_dir + '/' + file_name + '_params_names.txt', 'w') as fout:
                fout.write(','.join(['PARAM_' + b.upper() for b in bounds]))

    except Exception as e:
        print('\t', e)


if __name__ == "__main__":
    main()
