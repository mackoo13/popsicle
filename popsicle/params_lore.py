import math
import argparse
import os

from popsicle.ml_utils.df_utils import get_df_meta
from popsicle.utils import check_config


def intermediate_value(k, k_max, n_params, max_param):
    return int(math.pow(k / k_max, 1/n_params) * max_param)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n_values", type=int, help="Number of values to generate")
    parser.add_argument('-u', '--unroll', action='store_true', help='Generate parameters for unroll speedup prediction')
    args = parser.parse_args()
    n_values = args.n_values
    unroll = args.unroll

    var_name = 'LORE_PROC_CLANG_PATH' if unroll else 'LORE_PROC_PATH'
    check_config([var_name])
    proc_dir = os.path.abspath(os.environ[var_name])

    dirs = os.listdir(proc_dir)
    n_dirs = len(dirs)

    parsed = 0
    failed = 0

    df_meta = get_df_meta()

    for i, file_name in enumerate(dirs):
        if not os.path.isdir(os.path.join(proc_dir, file_name)):
            failed += 1
            continue

        print('[' + str(i) + '/' + str(n_dirs) + '] Generating params for ' + file_name)

        try:
            with open(os.path.join(proc_dir, file_name, file_name + '_params.txt'), 'w') as fout, \
                    open(os.path.join(proc_dir, file_name, file_name + '_params_names.txt'), 'r') as fin_names, \
                    open(os.path.join(proc_dir, file_name, file_name + '_max_param.txt'), 'r') as fin_max:

                max_param = int(fin_max.read())
                param_names = fin_names.read().strip().split(',')
                try:
                    loop_depth = df_meta.loc[file_name, 'loop_depth']
                except KeyError:
                    print('\tCannot generate params - unknown loop depth')
                    failed += 1
                    continue

                if len(param_names) > 0 and len(param_names[0]) > 0:
                    for k in range(1, n_values + 1):
                        defines = ['-D ' + p + '=' + str(intermediate_value(k, n_values, loop_depth, max_param))
                                   for p in param_names]
                        fout.write(' '.join(defines) + '\n')
                else:
                    fout.write('\n')

                parsed += 1

        except FileNotFoundError:
            failed += 1
            print('\tFile (...)_params_names.txt or (...)_max_param.txt is missing.')

    print('========')
    print(str(parsed) + ' parsed, ' + str(failed) + ' skipped')


if __name__ == "__main__":
    main()
