import os
import sys
import re


class ProcCodeTransformer:
    def __init__(self, includes, code):
        self.includes = includes
        self.code = code

    def add_includes(self, define_max=True):
        """
        Adds all necessary #include instructions to the code.
        """
        self.includes += '\n'
        self.includes += '#include <papi.h>\n'
        self.includes += '#include <time.h>\n'
        self.includes += '#include "' + os.path.abspath(os.path.dirname(sys.argv[0])) + '/../papi/papi_utils.h"\n'
        if define_max:
            self.includes += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'

    def add_papi(self):
        """
        Adds PAPI instructions in the places indicated by #pragma.
        """
        self.code, scop_count = re.subn(
            r'(#pragma scop\s+)', r'\1exec(PAPI_start(set));\n*begin = clock();\n',
            self.code)

        self.code, endscop_count = re.subn(
            r'(\s+#pragma endscop\s+)', r'\n*end = clock();\nexec(PAPI_stop(set, values));\1return 0;\n',
            self.code)

        if scop_count != 1 or endscop_count != 1:
            raise Exception('Exactly one "#pragma scop" and one "#pragma endscop" expected - found ' +
                            str(scop_count) + ' and ' + str(endscop_count) + ' correspondingly.')

    def add_pragma_macro(self):
        """
        todo
        """
        self.includes += '#define PRAGMA(p) _Pragma(p)\n'

    def arr_to_ptr_decl(self, dtypes, dims):
        """
        Replaces all fixed-size array declarations with pointer declarations.

        Example; 'int A[42][42];' -> 'int** A;'
        :param dtypes: (map: array_name: str -> data type: str)
        :param dims: A map from fixed-length arrays to their dimensions (map: array_name: str -> data type: str[])
        """
        for arr in dims:
            self.code = re.sub(
                r'(' + dtypes[arr] + ')\s+(' + arr + ').*;', r'\1' + '*' * dims[arr] + ' ' + arr + ';',
                self.code)

    def remove_bound_decl(self, bounds, dtypes):
        """
        todo
        :param dtypes:
        :param bounds:
        """
        for b in bounds:
            self.code = re.sub(r'(\b' + dtypes[b] + ' ' + b + ';)', r'//\1', self.code)

    def remove_pragma_semicolon(self):
        """
        Removes the semicolon after PRAGMA macro (added unintentionally by pycparser)
        """
        self.code = re.sub(r'(PRAGMA\(.*\));', r'\1', self.code)

    def rename_main(self):
        self.code = re.sub(r'\bmain\(', 'main_original(', self.code)

    def sub_loop_header(self):
        """
        Transforms the loop function header.
        """
        self.code, count = re.subn(
            r'void loop\(\)', 'int loop(int set, long_long* values, clock_t* begin, clock_t* end)',
            self.code)
        self.code = re.sub(r'return\s*;', 'return 0;', self.code)   # todo same in pp

        if count == 0:
            raise Exception('No "void loop()" function found')
