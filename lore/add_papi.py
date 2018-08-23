from __future__ import print_function
import argparse

from proc_utils import split_code, sub_loop_header, add_papi, add_includes


def transform(code):
    """
    Transforms code.
    :param code: C code (as string)
    :return: Transformed code
    """
    includes, code = split_code(code)

    includes = add_includes(includes)

    code = add_papi(code)
    code = sub_loop_header(code)
    code = includes + code
    return code


def main():

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("file_path", help="File path")
        args = parser.parse_args()
        file_path = args.file_path

        with open(file_path, 'r') as fin:
            code = fin.read()
            code = transform(code)

            with open(file_path, 'w') as fout:
                fout.write(code)

    except Exception as e:
        print('\t', e)


if __name__ == "__main__":
    main()
