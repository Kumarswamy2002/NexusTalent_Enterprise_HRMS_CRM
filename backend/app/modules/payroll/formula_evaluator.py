"""
NexusTalent Safe Formula Evaluator
AST-based Mathematical Parser for Dynamic Salary & Allowance Formulas.
Guarantees sandbox security (Zero arbitrary code execution / No eval()).
"""

import ast
import operator
from typing import Dict, Any

# Safe operators whitelist
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class FormulaEvaluationError(Exception):
    pass


class SafeFormulaEvaluator:

    @classmethod
    def evaluate(cls, expression: str, variables: Dict[str, float]) -> float:
        """
        Safely evaluates mathematical expressions like 'BASIC * 0.40' or 'CTC - (BASIC + HRA)'.
        """
        if not expression or not expression.strip():
            return 0.0

        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = cls._eval_node(tree.body, variables)
            return float(result)
        except Exception as e:
            raise FormulaEvaluationError(f"Formula error in '{expression}': {str(e)}")

    @classmethod
    def _eval_node(cls, node: ast.AST, variables: Dict[str, float]) -> float:
        if isinstance(node, ast.Constant):  # Python 3.8+ numbers
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise FormulaEvaluationError(f"Disallowed constant type: {type(node.value)}")

        elif isinstance(node, ast.Name):
            var_name = node.id.upper()
            lookup = {k.upper(): v for k, v in variables.items()}
            if var_name in lookup:
                return float(lookup[var_name])
            raise FormulaEvaluationError(f"Unknown variable in formula: {node.id}")

        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, variables)
            right = cls._eval_node(node.right, variables)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise FormulaEvaluationError(f"Unsupported mathematical operator: {op_type}")
            return SAFE_OPERATORS[op_type](left, right)

        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, variables)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise FormulaEvaluationError(f"Unsupported unary operator: {op_type}")
            return SAFE_OPERATORS[op_type](operand)

        else:
            raise FormulaEvaluationError(f"Unsupported expression node: {type(node).__name__}")
