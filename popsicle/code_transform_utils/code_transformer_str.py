import os
import re
from popsicle.utils import check_config

check_config('PAPI_UTILS_PATH')
papi_utils_path = os.path.abspath(os.environ['PAPI_UTILS_PATH'])


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

        self.includes += '#include "' + os.path.abspath(os.path.join(papi_utils_path, 'papi_utils.h')) + '"\n'

    def add_max_macro(self):
        self.includes += '#define MAX(x, y) (((x) > (y)) ? (x) : (y))\n'

    def add_pragma_macro(self):
        """
        Adds a macro to expand PRAGMA(PRAGMA_UNROLL);
        """
        self.includes += '#define PRAGMA(p) _Pragma(p)\n'

    def remove_pragma_semicolon(self):
        """
        Removes the semicolon after PRAGMA macro (side effect of by pycparser)
        """
        self.code = re.sub(r'(PRAGMA\(.*\));', r'\1', self.code)

    def rename_main(self):
        self.code = re.sub(r'\bmain\(', 'main_original(', self.code)
        self.code = re.sub(r'\n\s*(main_original\()', 'int \1', self.code)
