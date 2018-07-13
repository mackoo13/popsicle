import re
import argparse


max_n = 10


def get_defines(code, dataset):
    frag = re.search('ifdef ' + dataset + '_DATASET(.*?)endif', code, re.DOTALL)
    if frag:
        defines = frag.groups()[0]
        names = re.findall('define (\S*) ', defines)
        values = re.findall('define \S* (.*)\n', defines)
        values = [int(v) for v in values]
        return values, names


def scale_vals(imini, imed, i):
    return int(((imini*(max_n-1-i)) + (imed*i)) / (max_n-1))


# todo if main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="File name")
    args = parser.parse_args()
    file = args.file_name

    with open('kernels_pb/' + file + '/' + file + '.h', 'r') as fin:
        code = fin.read()
    mini, names = get_defines(code, 'MEDIUM')
    med, _ = get_defines(code, 'LARGE')

    for i in range(max_n):
        vals = [scale_vals(imini, imed, i) for imini, imed in zip(mini, med)]
        opts = ['-D '+n+'='+str(v) for n, v in zip(names, vals)]
        print(' '.join(opts))


main()
