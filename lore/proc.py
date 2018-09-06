from __future__ import print_function
from pycparser import c_generator
from proc_ast_parser import ProcASTParser
from proc_code_transformer import ProcCodeTransformer
from proc_utils import split_code, save_max_dims, ParseException
import argparse
import os


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = argparser.parse_args()
    verbose = args.verbose
    orig_path = os.environ['LORE_ORIG_PATH']
    proc_path = os.environ['LORE_PROC_PATH']

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

            print('[' + str(i + 1) + '/' + str(n_dirs) + '] Parsing %s' % file_name)

            file_path = os.path.join(orig_path, file_name)
            file_name = str(file_name[:-2])
            out_dir = os.path.join(proc_path, file_name)

            with open(file_path, 'r') as fin:
                code = fin.read()
                includes, code = split_code(code)

                pp = ProcASTParser(code, verbose, main_name='loop')
                pp.analyse()
                pp.remove_modifiers(['extern', 'restrict'])
                pp.add_papi()
                pp.gen_mallocs()
                pp.add_bounds_init()
                pp.arr_to_ptr_decl()

                generator = c_generator.CGenerator()
                code = generator.visit(pp.ast)

                pt = ProcCodeTransformer(includes, code)
                pt.add_includes()
                pt.add_max_macro()

                code = pt.includes + pt.code

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                if len(pp.refs) == 0:
                    failed += 1
                    raise ParseException('No refs found - cannot determine max_arr_dim')

                with open(os.path.join(out_dir, file_name) + '.c', 'w') as fout:
                    fout.write(code)

                max_param, max_arr_dim = pp.find_max_param()
                with open(os.path.join(out_dir, file_name + '_max_param.txt'), 'w') as fout:
                    fout.write(str(int(max_param)))

                with open(os.path.join(out_dir, file_name + '_params_names.txt'), 'w') as fout:
                    fout.write(','.join(['PARAM_' + b.upper() for b in pp.bounds]))

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
