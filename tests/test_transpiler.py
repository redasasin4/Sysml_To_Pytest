"""
Unit tests for constraint transpiler
"""

import pytest
from sysml2pytest.transpiler import ConstraintTranspiler, TranspilationError


class TestConstraintTranspiler:
    """Test ConstraintTranspiler class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.transpiler = ConstraintTranspiler()

    def test_simple_comparison(self):
        """Test simple comparison operators"""
        result = self.transpiler.transpile("x >= 10")
        assert result.python_code == "x >= 10"
        assert "x" in result.referenced_variables

    def test_compound_and_constraint(self):
        """Test compound AND constraints"""
        result = self.transpiler.transpile("150 <= treeHeight and treeHeight <= 200")
        assert result.python_code == "150 <= treeHeight and treeHeight <= 200"
        assert "treeHeight" in result.referenced_variables
        assert result.operator_count >= 2

    def test_compound_or_constraint(self):
        """Test compound OR constraints"""
        result = self.transpiler.transpile("x < 0 or x > 100")
        assert result.python_code == "x < 0 or x > 100"
        assert "x" in result.referenced_variables

    def test_not_operator(self):
        """Test NOT operator"""
        result = self.transpiler.transpile("not isActive")
        assert "not" in result.python_code
        assert "isActive" in result.referenced_variables

    def test_implies_operator(self):
        """Test implies operator conversion"""
        result = self.transpiler.transpile("A implies B")
        # A implies B should become (not A) or B
        assert "(not (A)) or (B)" in result.python_code or "(not A) or B" in result.python_code

    def test_complex_implies(self):
        """Test complex implies expression"""
        result = self.transpiler.transpile("voltage > 4.25 implies not charging")
        assert "not" in result.python_code
        assert "voltage" in result.referenced_variables
        assert "charging" in result.referenced_variables

    def test_arithmetic_expression(self):
        """Test arithmetic in constraints"""
        result = self.transpiler.transpile("baseDiameter >= 0.15 * treeHeight")
        assert "baseDiameter" in result.referenced_variables
        assert "treeHeight" in result.referenced_variables
        assert "*" in result.python_code

    def test_parentheses(self):
        """Test expression with parentheses"""
        result = self.transpiler.transpile("(x > 10) and (y < 20)")
        assert "x" in result.referenced_variables
        assert "y" in result.referenced_variables

    def test_empty_expression_error(self):
        """Test that empty expression raises error"""
        with pytest.raises(TranspilationError):
            self.transpiler.transpile("")

    def test_whitespace_expression_error(self):
        """Test that whitespace-only expression raises error"""
        with pytest.raises(TranspilationError):
            self.transpiler.transpile("   ")

    def test_clean_expression(self):
        """Test expression cleaning"""
        result = self.transpiler.transpile("{ x >= 10 }")
        # Curly braces should be removed
        assert "{" not in result.python_code
        assert "}" not in result.python_code

    def test_variable_extraction_excludes_keywords(self):
        """Test that Python keywords are not extracted as variables"""
        result = self.transpiler.transpile("x and y or not z")
        assert "x" in result.referenced_variables
        assert "y" in result.referenced_variables
        assert "z" in result.referenced_variables
        assert "and" not in result.referenced_variables
        assert "or" not in result.referenced_variables
        assert "not" not in result.referenced_variables

    def test_transpile_to_assertion(self):
        """Test transpilation to assertion statement"""
        assertion = self.transpiler.transpile_to_assertion("x >= 10")
        assert assertion.startswith("assert ")
        assert "x >= 10" in assertion

    def test_transpile_to_assertion_negated(self):
        """Test transpilation to negated assertion"""
        assertion = self.transpiler.transpile_to_assertion("x >= 10", negate=True)
        assert assertion.startswith("assert ")
        assert "not" in assertion

    def test_transpile_to_hypothesis_assume(self):
        """Test transpilation to Hypothesis assume call"""
        assume_code = self.transpiler.transpile_to_hypothesis_assume("x >= 0")
        assert "hypothesis.assume" in assume_code
        assert "x >= 0" in assume_code

    def test_generate_python_function(self):
        """Test generating Python function from constraint"""
        func_code = self.transpiler.generate_python_function(
            expression="x >= 10 and x <= 20",
            function_name="validate_range",
            parameters=["x"]
        )
        assert "def validate_range(x)" in func_code
        assert "return" in func_code
        assert "x >= 10 and x <= 20" in func_code

    def test_equality_operator(self):
        """Test equality operator"""
        result = self.transpiler.transpile("status == 'active'")
        assert "==" in result.python_code

    def test_inequality_operator(self):
        """Test inequality operator"""
        result = self.transpiler.transpile("status != 'inactive'")
        assert "!=" in result.python_code

    def test_less_than_operator(self):
        """Test less than operator"""
        result = self.transpiler.transpile("temperature < 100")
        assert "<" in result.python_code
        assert "temperature" in result.referenced_variables

    def test_greater_than_operator(self):
        """Test greater than operator"""
        result = self.transpiler.transpile("temperature > 0")
        assert ">" in result.python_code

    def test_multiple_variables(self):
        """Test extraction of multiple variables"""
        result = self.transpiler.transpile("x + y >= z * w")
        assert "x" in result.referenced_variables
        assert "y" in result.referenced_variables
        assert "z" in result.referenced_variables
        assert "w" in result.referenced_variables

    def test_floating_point_numbers(self):
        """Test constraints with floating point numbers"""
        result = self.transpiler.transpile("temperature >= -10.5 and temperature <= 50.5")
        assert "temperature" in result.referenced_variables
        assert "-10.5" in result.python_code or "-10.5" in result.original_expression
        assert "50.5" in result.python_code or "50.5" in result.original_expression

    def test_division_operator(self):
        """Test division in constraints"""
        result = self.transpiler.transpile("ratio < total / count")
        assert "/" in result.python_code
        assert "ratio" in result.referenced_variables
        assert "total" in result.referenced_variables
        assert "count" in result.referenced_variables


class TestExpressionOptimizer:
    """Test ExpressionOptimizer class"""

    def test_double_negation(self):
        """Test double negation simplification"""
        from sysml2pytest.transpiler.transpiler import ExpressionOptimizer

        simplified = ExpressionOptimizer.simplify("(not (not x))")
        assert simplified == "x"

    def test_and_true(self):
        """Test 'and True' simplification"""
        from sysml2pytest.transpiler.transpiler import ExpressionOptimizer

        simplified = ExpressionOptimizer.simplify("x and True")
        assert simplified == "x"

    def test_or_false(self):
        """Test 'or False' simplification"""
        from sysml2pytest.transpiler.transpiler import ExpressionOptimizer

        simplified = ExpressionOptimizer.simplify("x or False")
        assert simplified == "x"
