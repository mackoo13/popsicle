import os
import sys
import re


class CodeTransformerStr:
    def __init__(self, includes, code):
        self.includes = includes
        self.code = code

    def add_includes(self, other_includes=None):
        """
        Adds all necessary #include instructions to the code.
        """
        if other_includes is None:
            other_includes = []

        self.includes += '\n'
        self.includes += '#include <papi.h>\n'
        self.includes += '#include <time.h>\n'

        for path in other_includes:
            self.includes += '#include <' + path + '>\n'

        current_dir = os.path.dirname(sys.argv[0])
        self.includes += '#include "' + os.path.abspath(os.path.join(current_dir, '../papi/papi_utils.h')) + '"\n'

    def add_max_macro(self):
        self.includes += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'

    def add_pragma_macro(self):
        """
        todo
        """
        self.includes += '#define PRAGMA(p) _Pragma(p)\n'

    def remove_pragma_semicolon(self):
        """
        Removes the semicolon after PRAGMA macro (added unintentionally by pycparser)
        """
        self.code = re.sub(r'(PRAGMA\(.*\));', r'\1', self.code)

    def rename_main(self):
        self.code = re.sub(r'\bmain\(', 'main_original(', self.code)
        self.code = re.sub(r'\n\s*(main_original\()', 'int \1', self.code)
