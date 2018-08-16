from __future__ import print_function


from pycparser import c_parser
from lore import lore_parser
import os
import argparse

from lore_proc_utils import add_includes, add_papi, split_code, sub_loop_header, del_extern_restrict, gen_mallocs, \
    arr_to_ptr_decl, add_mallocs, find_max_param


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

            if lore_parser.contains_struct(code):
                raise lore_parser.ParseException('Code contains struct declaration.')

            parser = c_parser.CParser()
            ast = parser.parse(code)

            if verbose:
                ast.show()

            includes = add_includes(includes)

            bounds, refs, dtypes, dims = lore_parser.analyze(ast, verbose)
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
                raise lore_parser.ParseException('No refs found - cannot determine max_arr_dim')

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
