from __future__ import print_function
from popsicle.code_transform_utils.code_transformer import CodeTransformer
from popsicle.code_transform_utils.code_transform_utils import split_code
import argparse
import os
from popsicle.utils import check_config
import pandas as pd


def main():
    check_config(['LORE_ORIG_PATH', 'LORE_PROC_PATH'])

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    argparser.add_argument('-u', '--unroll', action='store_true', help='If enabled prepare code for loop unrolling')
    args = argparser.parse_args()
    verbose = args.verbose
    unroll = args.unroll
    orig_path = os.path.abspath(os.environ['LORE_ORIG_PATH'])
    proc_path = os.path.abspath(os.environ['LORE_PROC_PATH'])

    df_meta = pd.DataFrame(columns=('alg', 'max_arr_dim', 'loop_depth'))
    print(df_meta)

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

                ct = CodeTransformer(
                    includes=includes,
                    code=code,
                    papi_scope='pragma',
                    verbose=verbose,
                    main_name='loop',
                    modifiers_to_remove=['extern'],
                    gen_mallocs=True,
                    rename_bounds=(not unroll),
                    add_pragma_unroll=unroll
                )

                code = ct.transform()

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                with open(os.path.join(out_dir, file_name + '.c'), 'w') as fout:
                    fout.write(code)

                with open(os.path.join(out_dir, file_name + '_max_param.txt'), 'w') as fout:
                    fout.write(str(ct.max_param))

                with open(os.path.join(out_dir, file_name + '_params_names.txt'), 'w') as fout:
                    fout.write(','.join(['PARAM_' + b.upper() for b in ct.pp.bounds]))

                df_meta = df_meta.append(pd.DataFrame(
                    [[file_name, ct.max_arr_dim, ct.loop_depth]],
                    columns=df_meta.columns
                ), ignore_index=True)

                parsed += 1

        except Exception as e:
            failed += 1
            print('\t', e)

    df_meta.to_csv(os.path.join(proc_path, 'metadata.csv'), index_label=False, index=False)

    print('========')
    print(str(parsed) + ' parsed, ' + str(failed) + ' skipped')


if __name__ == "__main__":
    main()
