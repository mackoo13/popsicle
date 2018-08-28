from __future__ import print_function

from pycparser import c_parser, c_generator
import os
import argparse

from proc_utils import add_includes, add_papi, split_code, sub_loop_header, del_extern_restrict, gen_mallocs, \
    arr_to_ptr_decl, add_mallocs, find_max_param, save_max_dims, remove_pragma_semicolon, add_pragma_macro, \
    remove_bound_decl
from parser import analyze, ParseException, StructVisitor
from parser_clang import add_pragma_unroll


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = argparser.parse_args()
    verbose = args.verbose
    orig_path = os.environ['LORE_ORIG_PATH']
    proc_path = os.environ['LORE_PROC_CLANG_PATH']

    max_arr_dims = {}

    if not os.path.isdir(proc_path):
        os.makedirs(proc_path)

    dirs = os.listdir(orig_path)
    n_dirs = len(dirs)
    parsed = 0
    failed = 0

    for i, file_name in enumerate(dirs):
        try:
            if not file_name.endswith(".c"):
                continue

            print('[' + str(i) + '/' + str(n_dirs) + '] Parsing %s' % file_name)

            file_name = str(file_name[:-2])
            out_dir = os.path.join(proc_path, file_name)

            with open(os.path.join(orig_path, file_name + '.c'), 'r') as fin:
                code = fin.read()
                includes, code = split_code(code)

                # if lore_parser_clang.contains_struct(code):
                #     pass
                #     raise lore_parser_clang.ParseException('Code contains struct declaration.')

                argparser = c_parser.CParser()
                ast = argparser.parse(code)

                sv = StructVisitor()
                sv.visit(ast)
                if sv.contains_struct:
                    print('\tSkipping ' + file_name + ' - contains struct')
                    failed += 1
                    continue

                if verbose:
                    ast.show()

                add_pragma_unroll(ast)
                generator = c_generator.CGenerator()
                code = generator.visit(ast)
                code = remove_pragma_semicolon(code)

                includes = add_includes(includes)
                includes = add_pragma_macro(includes)

                bounds, refs, dtypes, dims = analyze(ast, verbose)
                mallocs = gen_mallocs(refs, dtypes)

                code = del_extern_restrict(code)
                code = arr_to_ptr_decl(code, dtypes, dims)
                code = add_papi(code)
                code = add_mallocs(code, mallocs)
                code = sub_loop_header(code)
                code = remove_bound_decl(code, bounds, dtypes)
                code = includes + code

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                if len(refs) == 0:
                    failed += 1
                    raise ParseException('No refs found - cannot determine max_arr_dim')

                with open(out_dir + '/' + file_name + '.c', 'w') as fout:
                    fout.write(code)

                max_param, max_arr_dim = find_max_param(refs, ast, verbose)
                with open(out_dir + '/' + file_name + '_max_param.txt', 'w') as fout:
                    fout.write(str(int(max_param)))

                with open(out_dir + '/' + file_name + '_params_names.txt', 'w') as fout:
                    # fout.write(','.join(bounds))
                    fout.write(','.join(bounds))

                max_arr_dims[file_name] = max_arr_dim

                parsed += 1

        except Exception as e:
            failed += 1
            print('\t', e)

    save_max_dims(proc_path, max_arr_dims)

    print('========')
    print(str(parsed) + ' parsed, ' + str(failed) + ' skipped')


if __name__ == "__main__":
    main()
