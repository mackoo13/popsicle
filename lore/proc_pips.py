from __future__ import print_function
from pycparser import c_generator
from proc_ast_parser import ProcASTParser
from proc_code_transformer import ProcCodeTransformer
from proc_utils import remove_inline, remove_comments
import argparse
import os


def main():
    if 'PIPS_PROC_PATH' not in os.environ:
        raise EnvironmentError

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = argparser.parse_args()
    verbose = args.verbose
    proc_path = os.environ['PIPS_PROC_PATH']

    if not os.path.isdir(proc_path):
        os.makedirs(proc_path)

    for path, _, file_names in os.walk(proc_path):
        for file_name in file_names:
            try:
                if not file_name.endswith(".c") \
                        or file_name.endswith("_preproc.c") \
                        or file_name.endswith("_wombat.c"):
                    continue

                print('Parsing %s' % file_name)

                file_path = os.path.join(path, file_name)
                preproc_path = file_path[:-2] + '_preproc.c'

                if not os.path.isfile(preproc_path):
                    continue

                with open(file_path, 'r') as fin_orig:
                    with open(preproc_path, 'r') as fin_preproc:
                        orig_code = fin_orig.read()
                        preproc_code = fin_preproc.read()

                        preproc_code = remove_comments(preproc_code)
                        preproc_code = remove_inline(preproc_code)

                        pp = ProcASTParser(preproc_code, verbose, allow_struct=True)
                        pp.remove_modifiers(['extern'])
                        pp.single_to_compound()
                        pp.main_to_loop()

                        generator = c_generator.CGenerator()
                        code_main = generator.visit(pp.main)

                        pt = ProcCodeTransformer('', '')
                        pt.add_includes()

                        pt_orig = ProcCodeTransformer('', orig_code)
                        pt_orig.rename_main()

                        code = pt.includes + '\n\n' + pt_orig.code + '\n\n' + code_main

                        with open(file_path[:-2] + '_wombat.c', 'w') as fout:
                            fout.write(code)

            except Exception as e:
                print('\t', e)


if __name__ == "__main__":
    main()
