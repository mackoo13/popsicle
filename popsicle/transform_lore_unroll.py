from __future__ import print_function
from popsicle.code_transform_utils.code_transformer import CodeTransformer
from popsicle.code_transform_utils.code_transform_utils import split_code, save_max_dims
import os
import argparse
from popsicle.utils import check_config


def main():
    check_config(['LORE_ORIG_PATH', 'LORE_PROC_CLANG_PATH'])

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

                ct = CodeTransformer(
                    includes=includes,
                    code=code,
                    papi_scope='pragma',
                    main_name='loop',
                    verbose=verbose,
                    modifiers_to_remove=['extern', 'restrict'],
                    add_pragma_unroll=True,
                    gen_mallocs=True,
                )

                code = ct.transform()

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                with open(os.path.join(out_dir, file_name + '.c'), 'w') as fout:
                    fout.write(code)

                with open(os.path.join(out_dir, file_name + '_max_param.txt'), 'w') as fout:
                    fout.write(str(ct.max_param))

                with open(os.path.join(out_dir, file_name + '_params_names.txt'), 'w') as fout:
                    fout.write(','.join(ct.pp.bounds))

                max_arr_dims[file_name] = ct.max_arr_dim

                parsed += 1

        except Exception as e:
            failed += 1
            print('\t', e)

    save_max_dims(proc_path, max_arr_dims)

    print('========')
    print(str(parsed) + ' parsed, ' + str(failed) + ' skipped')


if __name__ == "__main__":
    main()
