import math
import argparse
import os

from popsicle.utils import check_config


def intermediate_value(k, k_max, n_params, max_param):
    return int(math.pow(k / k_max, 1/n_params) * max_param)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("k", type=int, help="Number of distinct parameters")
    parser.add_argument('-u', '--unroll', action='store_true', help='Verbose')
    args = parser.parse_args()
    k_max = args.k
    unroll = args.unroll

    var_name = 'LORE_PROC_CLANG_PATH' if unroll else 'LORE_PROC_PATH'
    check_config([var_name])
    proc_dir = os.environ[var_name]

    dirs = os.listdir(proc_dir)
    n_dirs = len(dirs)

    parsed = 0
    failed = 0

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

                if len(param_names) > 0 and len(param_names[0]) > 0:

                    for k in range(1, k_max + 1):
                        defines = ['-D ' + p + '=' + str(intermediate_value(k, k_max, len(param_names), max_param))
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
