from __future__ import print_function
from popsicle.code_transform_utils.code_transformer import CodeTransformer
from popsicle.code_transform_utils.code_transform_utils import split_code
import argparse


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('file_path', type=str, help='input file todo')
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = argparser.parse_args()
    verbose = args.verbose
    file_path = args.file_path

    try:
        print('Parsing %s' % file_path)

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
                gen_mallocs=False,
            )

            code = ct.transform()

            with open(file_path + '_papi.c', 'w') as fout:
                fout.write(code)

    except Exception as e:
        print('\t', e)


if __name__ == "__main__":
    main()
