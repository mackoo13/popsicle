import math
import argparse


def intermediate_value(k, n_params, max_param):
    return int(math.pow(k/10, 1/n_params) * max_param)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="File name")
    args = parser.parse_args()
    file_name = args.file_name

    kernels_path = '../kernels_lore/'
    out_dir = kernels_path + 'proc/' + file_name

    with open(out_dir + '/' + file_name + '_params.txt', 'w') as fout, \
            open(out_dir + '/' + file_name + '_params_names.txt', 'r') as fin_names, \
            open(out_dir + '/' + file_name + '_max_param.txt', 'r') as fin_max:

        max_param = int(fin_max.read())
        param_names = fin_names.read().strip().split(',')

        if len(param_names) > 0 and len(param_names[0]) > 0:

            for k in range(1, 31):
                defines = [f'-D {p}={str(intermediate_value(k, len(param_names), max_param))}' for p in param_names]
                fout.write(' '.join(defines) + '\n')
        else:
            fout.write('\n')


main()
