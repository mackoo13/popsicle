from __future__ import print_function
import re
import os
import sys
import argparse


def split_code(code):
    """
    Splits code into the section containing macros and the rest of the code.
    :param code: C code (as string)
    :return: Transformed code
    """
    return re.split(r'\n(?!#)', code, 1)


def add_includes(includes):
    """
    Adds all necessary #include instructions to the code.
    :param includes: C code section containing #include's (as string)
    :return: Transformed code
    """
    res = includes + '\n'
    res += '#include <papi.h>\n'
    res += '#include <time.h>\n'
    res += '#include "' + os.path.abspath(os.path.dirname(sys.argv[0])) + '/../papi_utils/papi_events.h"\n'
    return res


def add_papi(code):
    """
    Adds PAPI instructions in the places indicated by #pragma.
    :param code: C code (as string)
    :return: Transformed code
    """
    code = re.sub(r'(#pragma scop\n)', r'\1exec(PAPI_start(set));\n*begin = clock();', code)
    code = re.sub(r'(\n#pragma endscop\n)', r'\n*end = clock();\nexec(PAPI_stop(set, values));\1return 0;\n', code)
    return code


def sub_loop_header(code):
    """
    Transforms the loop function header.
    :param code: C code (as string)
    :return: Transformed code
    """
    code = re.sub(r'void loop\(\)', 'int loop(int set, long_long* values, clock_t* begin, clock_t* end)', code)
    code = re.sub(r'return\s*;', 'return 0;', code)
    return code


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
