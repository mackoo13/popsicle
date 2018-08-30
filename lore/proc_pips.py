from __future__ import print_function
from pycparser import c_parser, c_generator
from proc_ast_parser import ProcASTParser
from proc_code_transformer import ProcCodeTransformer
from proc_utils import remove_inline, remove_comments
import argparse
import os


def main():
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
                if not file_name.endswith("_preproc.c"):
                    continue

                print('Parsing %s' % file_name)

                file_path = os.path.join(path, file_name)

                with open(file_path, 'r') as fin:
                    code = fin.read()
                    code = remove_comments(code)
                    code = remove_inline(code)

                    astparser = c_parser.CParser()
                    ast = astparser.parse(code)
                    pp = ProcASTParser(ast, verbose, allow_struct=True)
                    pp.remove_extern()
                    pp.main_to_loop()

                    generator = c_generator.CGenerator()
                    code = generator.visit(ast)

                    pt = ProcCodeTransformer('', code)
                    pt.add_includes()
                    pt.arr_to_ptr_decl(pp.dtypes, pp.dims)

                    code = pt.includes + pt.code

                    with open(file_path[:-2] + '_wombat.c', 'w') as fout:
                        fout.write(code)

            except Exception as e:
                print('\t', e)


if __name__ == "__main__":
    main()
