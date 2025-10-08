"""
Transpiler for converting SysML V2 constraint expressions to Python
"""

import re
import logging
from typing import Dict, Set, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TranspilationError(Exception):
    """Error during constraint transpilation"""
    pass


@dataclass
class TranspiledConstraint:
    """Result of transpiling a constraint expression"""
    python_code: str
    referenced_variables: Set[str]
    operator_count: int
    original_expression: str


class ConstraintTranspiler:
    """
    Transpiles SysML V2 constraint expressions to Python code

    Handles:
    - Comparison operators: <=, >=, ==, !=, <, >
    - Logical operators: and, or, not
    - Arithmetic operators: +, -, *, /
    - Parentheses and precedence
    - Attribute/variable references
    """

    # Operator mappings from SysML V2 to Python
    OPERATOR_MAP = {
        "and": "and",
        "or": "or",
        "not": "not",
        "implies": "not {0} or {1}",  # A implies B == (not A) or B
        "==": "==",
        "!=": "!=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "/",
        "in": "in",
    }

    def __init__(self):
        """Initialize transpiler"""
        self.variable_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')

    def transpile(self, expression: str) -> TranspiledConstraint:
        """
        Transpile SysML V2 constraint expression to Python

        Args:
            expression: SysML V2 constraint expression

        Returns:
            TranspiledConstraint with Python code and metadata

        Raises:
            TranspilationError: If expression cannot be transpiled
        """
        if not expression or not expression.strip():
            raise TranspilationError("Empty expression")

        try:
            # Clean and normalize expression
            cleaned = self._clean_expression(expression)

            # Handle 'implies' operator specially
            if "implies" in cleaned:
                cleaned = self._handle_implies(cleaned)

            # Transpile to Python
            python_code = self._transpile_expression(cleaned)

            # Extract referenced variables
            variables = self._extract_variables(python_code)

            # Count operators
            op_count = self._count_operators(python_code)

            return TranspiledConstraint(
                python_code=python_code,
                referenced_variables=variables,
                operator_count=op_count,
                original_expression=expression
            )

        except Exception as e:
            raise TranspilationError(f"Failed to transpile '{expression}': {e}")

    def _clean_expression(self, expr: str) -> str:
        """Clean and normalize expression"""
        # Remove extra whitespace
        expr = " ".join(expr.split())

        # Remove curly braces often used in SysML constraints
        expr = expr.replace("{", "").replace("}", "")

        return expr.strip()

    def _handle_implies(self, expr: str) -> str:
        """
        Handle 'implies' operator

        A implies B  →  (not A) or B
        """
        # Simple regex to find 'implies' and split
        # This is a simplified version; full parser would handle nested cases
        if " implies " in expr:
            parts = expr.split(" implies ", 1)
            if len(parts) == 2:
                left, right = parts
                return f"(not ({left.strip()})) or ({right.strip()})"

        return expr

    def _transpile_expression(self, expr: str) -> str:
        """
        Transpile expression to Python

        This is a simplified transpiler that handles common cases.
        A full implementation would use a proper parser (e.g., Lark).
        """
        python_expr = expr

        # No operator replacement needed for most cases
        # SysML V2 uses Python-compatible syntax for basic expressions

        return python_expr

    def _extract_variables(self, expr: str) -> Set[str]:
        """Extract variable names from expression"""
        # Find all identifiers
        identifiers = self.variable_pattern.findall(expr)

        # Filter out Python keywords and operators
        python_keywords = {
            "and", "or", "not", "True", "False", "None",
            "if", "else", "elif", "for", "while", "in", "is"
        }

        variables = {
            var for var in identifiers
            if var not in python_keywords
        }

        return variables

    def _count_operators(self, expr: str) -> int:
        """Count operators in expression"""
        count = 0
        operators = ["<=", ">=", "==", "!=", "<", ">", " and ", " or ", " not "]

        for op in operators:
            count += expr.count(op)

        return count

    def transpile_to_assertion(self, expression: str, negate: bool = False) -> str:
        """
        Transpile to Python assertion statement

        Args:
            expression: SysML V2 constraint expression
            negate: Whether to negate the assertion (for negative tests)

        Returns:
            Python assert statement
        """
        result = self.transpile(expression)
        code = result.python_code

        if negate:
            code = f"not ({code})"

        return f"assert {code}"

    def transpile_to_hypothesis_assume(self, expression: str) -> str:
        """
        Transpile to Hypothesis assume() call

        Args:
            expression: SysML V2 constraint expression (typically an assume constraint)

        Returns:
            Python code: hypothesis.assume(expression)
        """
        result = self.transpile(expression)
        return f"hypothesis.assume({result.python_code})"

    def generate_python_function(
        self,
        expression: str,
        function_name: str,
        parameters: List[str]
    ) -> str:
        """
        Generate a Python function that evaluates the constraint

        Args:
            expression: SysML V2 constraint expression
            function_name: Name for the generated function
            parameters: List of parameter names

        Returns:
            Python function definition as string
        """
        result = self.transpile(expression)

        param_str = ", ".join(parameters)
        code = f"""def {function_name}({param_str}) -> bool:
    \"\"\"
    Constraint: {result.original_expression}
    \"\"\"
    return {result.python_code}
"""
        return code


class ExpressionOptimizer:
    """Optimizes transpiled Python expressions"""

    @staticmethod
    def simplify(expr: str) -> str:
        """
        Simplify redundant expressions

        Examples:
            (not (not x)) → x
            x and True → x
            x or False → x
        """
        # Remove double negation
        expr = re.sub(r'\(not \(not ([^)]+)\)\)', r'\1', expr)

        # Simplify True/False
        expr = re.sub(r'([a-zA-Z_]\w*) and True', r'\1', expr)
        expr = re.sub(r'True and ([a-zA-Z_]\w*)', r'\1', expr)
        expr = re.sub(r'([a-zA-Z_]\w*) or False', r'\1', expr)
        expr = re.sub(r'False or ([a-zA-Z_]\w*)', r'\1', expr)

        return expr
