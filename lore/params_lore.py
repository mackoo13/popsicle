import math
import argparse
import os


def intermediate_value(k, k_max, n_params, max_param):
    return int(math.pow(k / k_max, 1/n_params) * max_param)


def main():
    if 'LORE_PROC_PATH' not in os.environ:
        raise EnvironmentError

    parser = argparse.ArgumentParser()
    parser.add_argument("k", type=int, help="Number of distinct parameters")
    args = parser.parse_args()
    k_max = args.k
    proc_dir = os.environ['LORE_PROC_PATH']

    for file_name in os.listdir(proc_dir):
        if not os.path.isdir(os.path.join(proc_dir, file_name)):
            continue

        print('Generating params for ' + file_name)

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
        except FileNotFoundError:
            print('\t' + file_name + '_params_names.txt or ' + file_name + '_max_param.txt is missing.')


if __name__ == "__main__":
    main()
