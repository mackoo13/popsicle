from typing import Set, Mapping, List, Iterable
from pycparser import c_ast

from wombat.code_transform_utils.exceptions import ParseException


def remove_non_extreme_numbers(s: Iterable[str], leave_min=True) -> Iterable[str]:
    """
    Removes from an iterable all numbers which are neither minimal or maximal.
    All non-numeric elements are left untouched.
    The order of elements might be different in the output.

    Example: ['3', '6', 'N', '7'] -> ['N', '3', '7']
    :param s: Iterable of expressions as strings
    :param leave_min: If set to True, preserve minimal and maximum value from s. Otherwise, only maximum is preserved.
    :return: Transformed iterable
    """
    max_num = float('-inf')
    min_num = 0
    res = []

    for el in s:
        if type(el) is str and el.isdecimal():
            el_num = int(el)
            min_num = min(min_num, el_num)
            max_num = max(max_num, el_num)
        elif el is not None:
            res.append(el)

    if max_num > 0:
        res.append(str(max_num))
    if leave_min and min_num > 0 and min_num != max_num:
        res.append(str(min_num))

    return res


def eval_basic_op(l: str, op: str, r: str) -> str:
    """
    Evaluate a basic arithmetic operation
    :param l: Left operand
    :param op: Operator
    :param r: Right operand
    :return: Result or a string representing the operation if it cannot be calculated
    """
    if l.isdecimal() and r.isdecimal():
        l_num = int(l)
        r_num = int(r)
        if op == '+':
            return str(l_num + r_num)
        if op == '-':
            return str(l_num - r_num)
        if op == '*':
            return str(l_num * r_num)

    return l + op + r


class ExprEstimator:
    def __init__(self,
                 maxs: Mapping[str, Set[str]]=None,
                 var: str=None,
                 parent_calls: List[any]=None):

        """
        Attempts to find a set of expressions which *might* represent the maximal value of expr. The primary use of this
        function is determining the size of an array based on its uses in the code.

        :param maxs: A map containing possible upper bounds for variables
        :param var: Which variable is estimated. Used
        :param parent_calls: History of expressions from previous recurrent calls  - prevents infinite loop
        """
        
        self.maxs = {} if maxs is None else maxs
        self.parent_calls = [] if parent_calls is None else parent_calls
        self.var = var

    def estimate(self, expr: any) -> Set[str]:
        """
        :param expr: An expression to estimate
        :return: Set of C expressions which might evaluate to the maximal possible value of expr.
        """
    
        # prevent infinite loop
        if expr in self.parent_calls:
            return set()
        self.parent_calls.append(expr)
    
        # multiple options => take into account all of them
        if type(expr) is set or type(expr) is list:
            options = []
            for e in expr:
                options.extend(self.estimate(e))
    
        # variable name => check maxs (possible upper bounds)
        elif type(expr) is str:
            options = self.maxs[expr] if expr in self.maxs else [expr]
    
        # variable => subsequent call with type(expr)=str
        elif type(expr) is c_ast.ID:
            if self.var is not None and expr.name not in self.maxs:
                # size of an array depends on a variable whose value is unknown
                raise ParseException(
                    'Variable-dependent array size detected: size of ' + self.var + ' depends on ' + expr.name)
    
            options = self.estimate(expr.name)
    
        # binary operation => try to evaluate if possible
        elif type(expr) is c_ast.BinaryOp:
            ls = self.estimate(expr.left)
            rs = self.estimate(expr.right)
            options = [eval_basic_op(l, expr.op, r) for l in ls for r in rs]
    
        # constant => take value
        elif type(expr) is c_ast.Constant:
            options = [expr.value]
    
        # unsupported object
        else:
            options = []
    
        options = remove_non_extreme_numbers(options)
        return set(options)
