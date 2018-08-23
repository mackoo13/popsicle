import math
import argparse


def intermediate_value(k, k_max, n_params, max_param):
    return int(math.pow(k / k_max, 1/n_params) * max_param)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="Dir path")
    parser.add_argument("k", type=int, help="Number of distinct parameters")
    args = parser.parse_args()
    proc_dir = args.dir
    k_max = args.k
    file_name = proc_dir.split('/')[-2]

    try:
        with open(proc_dir + file_name + '_params.txt', 'w') as fout, \
                open(proc_dir + file_name + '_params_names.txt', 'r') as fin_names, \
                open(proc_dir + file_name + '_max_param.txt', 'r') as fin_max:

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
        print(file_name + '_params_names.txt or ' + file_name + '_max_param.txt is missing.')


if __name__ == "__main__":
    main()
