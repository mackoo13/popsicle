from __future__ import print_function

from pycparser import c_parser
from proc_ast_parser import ProcASTParser
from proc_code_transformer import ProcCodeTransformer
from proc_utils import split_code, gen_mallocs, find_max_param, save_max_dims, add_bounds_init, ParseException
import argparse
import os


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = argparser.parse_args()
    verbose = args.verbose
    orig_path = os.environ['LORE_ORIG_PATH']
    proc_path = os.environ['LORE_PROC_PATH']

    max_arr_dims = {}

    if not os.path.isdir(proc_path):
        os.makedirs(proc_path)

    for file_name in os.listdir(orig_path):
        try:
            if not file_name.endswith(".c"):
                continue

            print('Parsing %s' % file_name)

            file_path = os.path.join(orig_path, file_name)
            file_name = str(file_name[:-2])
            out_dir = os.path.join(proc_path, file_name)

            with open(file_path, 'r') as fin:
                code = fin.read()
                includes, code = split_code(code)

                # if lore_parser.contains_struct(code):
                #     raise lore_parser.ParseException('Code contains struct declaration.')

                astparser = c_parser.CParser()
                ast = astparser.parse(code)
                pp = ProcASTParser(ast, verbose)
                pp.analyze(ast, verbose)

                pt = ProcCodeTransformer(includes, code)
                pt.add_includes()

                mallocs = gen_mallocs(pp.refs, pp.dtypes)
                mallocs = add_bounds_init(mallocs, pp.bounds)

                pt.del_extern_restrict()
                pt.arr_to_ptr_decl(pp.dtypes, pp.dims)
                pt.add_papi()
                pt.add_mallocs(mallocs)
                pt.sub_loop_header()

                code = pt.includes + pt.code

                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                if len(pp.refs) == 0:
                    raise ParseException('No refs found - cannot determine max_arr_dim')

                with open(out_dir + '/' + file_name + '.c', 'w') as fout:
                    fout.write(code)

                max_param, max_arr_dim = find_max_param(pp.refs, ast, verbose)
                with open(out_dir + '/' + file_name + '_max_param.txt', 'w') as fout:
                    fout.write(str(int(max_param)))

                with open(out_dir + '/' + file_name + '_params_names.txt', 'w') as fout:
                    fout.write(','.join(['PARAM_' + b.upper() for b in pp.bounds]))

                max_arr_dims[file_name] = max_arr_dim

        except Exception as e:
            print('\t', e)

    save_max_dims(proc_path, max_arr_dims)


if __name__ == "__main__":
    main()
