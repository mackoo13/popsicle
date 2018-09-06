from __future__ import print_function
from pycparser import c_generator
from proc_code_transformer import ProcCodeTransformer
from proc_utils import split_code, save_max_dims, ParseException
from proc_ast_parser import ProcASTParser
import os
import argparse


def main():
    if 'LORE_ORIG_PATH' not in os.environ or 'LORE_PROC_CLANG_PATH' not in os.environ:
        raise EnvironmentError

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

                pp = ProcASTParser(code, verbose)
                pp.analyse()
                pp.remove_modifiers(['extern', 'restrict'])
                pp.add_pragma_unroll()
                pp.add_papi()
                pp.gen_mallocs()
                pp.arr_to_ptr_decl()

                generator = c_generator.CGenerator()
                code = generator.visit(pp.ast)

                pt = ProcCodeTransformer(includes, code)
                pt.remove_pragma_semicolon()
                pt.add_includes()
                pt.add_max_macro()
                pt.add_pragma_macro()

                pt.remove_bound_decl(pp.bounds, pp.dtypes)

                code = includes + code

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                if len(pp.refs) == 0:
                    failed += 1
                    raise ParseException('No refs found - cannot determine max_arr_dim')    # todo move

                with open(out_dir + '/' + file_name + '.c', 'w') as fout:
                    fout.write(code)

                max_param, max_arr_dim = pp.find_max_param()
                with open(out_dir + '/' + file_name + '_max_param.txt', 'w') as fout:
                    fout.write(str(int(max_param)))

                with open(out_dir + '/' + file_name + '_params_names.txt', 'w') as fout:
                    fout.write(','.join(pp.bounds))

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
