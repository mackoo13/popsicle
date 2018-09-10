from __future__ import print_function
from code_transform_utils.code_transformer import CodeTransformer
from code_transform_utils.code_transformer_str import CodeTransformerStr
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

    dirs = os.listdir(proc_path)
    n_dirs = len(dirs)
    parsed = 0
    failed = 0

    for i, (path, _, file_names) in enumerate(os.walk(proc_path)):
        for file_name in file_names:
            try:
                if not file_name.endswith(".c") \
                        or file_name.endswith("_preproc.c") \
                        or file_name.endswith("_wombat.c"):
                    continue

                print('[' + str(i) + '/' + str(n_dirs) + '] Parsing %s' % file_name)

                file_path = os.path.join(path, file_name)
                preproc_path = file_path[:-2] + '_preproc.c'

                if not os.path.isfile(preproc_path):
                    continue

                with open(file_path, 'r') as fin_orig:
                    with open(preproc_path, 'r') as fin_preproc:
                        orig_code = fin_orig.read()
                        preproc_code = fin_preproc.read()

                        code_main = CodeTransformer(
                            includes='',
                            code=preproc_code,
                            papi_scope='function',
                            verbose=verbose,
                            allow_struct=True,
                            remove_comments=True,
                            remove_inline=True,
                            modifiers_to_remove=['extern'],
                            return_only_main=True
                        ).transform()

                        pt = CodeTransformerStr('', '')
                        pt.add_includes()

                        pt_orig = CodeTransformerStr('', orig_code)
                        pt_orig.rename_main()

                        code = pt.includes + '\n\n' + pt_orig.code + '\n\n' + code_main

                        with open(file_path[:-2] + '_wombat.c', 'w') as fout:
                            fout.write(code)

                        parsed += 1

            except Exception as e:
                failed += 1
                print('\t', e)


if __name__ == "__main__":
    main()
