"""
Unit tests for Hypothesis strategy generation
"""

import pytest
from sysml2pytest.transpiler import HypothesisStrategyGenerator
from sysml2pytest.extractor.models import RequirementAttribute, AttributeType


class TestHypothesisStrategyGenerator:
    """Test HypothesisStrategyGenerator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = HypothesisStrategyGenerator()

    def test_integer_strategy_unbounded(self):
        """Test integer strategy without bounds"""
        attr = RequirementAttribute(name="count", type=AttributeType.INTEGER)
        config = self.generator.generate_strategy(attr)

        assert "st.integers()" in config.strategy_code
        assert "unbounded" in config.description.lower()

    def test_integer_strategy_with_bounds(self, sample_integer_attribute):
        """Test integer strategy with min/max bounds"""
        config = self.generator.generate_strategy(sample_integer_attribute)

        assert "st.integers(" in config.strategy_code
        assert "min_value=150" in config.strategy_code
        assert "max_value=200" in config.strategy_code

    def test_integer_strategy_with_constraint_ranges(self):
        """Test integer strategy with constraint-derived ranges"""
        attr = RequirementAttribute(name="value", type=AttributeType.INTEGER)
        ranges = {"min": 10, "max": 100}

        config = self.generator.generate_strategy(attr, ranges)

        assert "min_value=10" in config.strategy_code
        assert "max_value=100" in config.strategy_code

    def test_real_strategy_unbounded(self):
        """Test real strategy without bounds"""
        attr = RequirementAttribute(name="temperature", type=AttributeType.REAL)
        config = self.generator.generate_strategy(attr)

        assert "st.floats(" in config.strategy_code
        assert "allow_nan=False" in config.strategy_code
        assert "allow_infinity=False" in config.strategy_code

    def test_real_strategy_with_bounds(self, sample_real_attribute):
        """Test real strategy with min/max bounds"""
        config = self.generator.generate_strategy(sample_real_attribute)

        assert "st.floats(" in config.strategy_code
        assert "min_value=-10.0" in config.strategy_code
        assert "max_value=50.0" in config.strategy_code
        assert "allow_nan=False" in config.strategy_code

    def test_boolean_strategy(self, sample_boolean_attribute):
        """Test boolean strategy"""
        config = self.generator.generate_strategy(sample_boolean_attribute)

        assert "st.booleans()" in config.strategy_code
        assert "Boolean" in config.description or "True/False" in config.description

    def test_string_strategy_default(self, sample_string_attribute):
        """Test string strategy with default settings"""
        config = self.generator.generate_strategy(sample_string_attribute)

        assert "st.text()" in config.strategy_code

    def test_string_strategy_with_length_constraints(self):
        """Test string strategy with length constraints"""
        attr = RequirementAttribute(name="name", type=AttributeType.STRING)
        ranges = {"min_length": 5, "max_length": 50}

        config = self.generator.generate_strategy(attr, ranges)

        assert "st.text(" in config.strategy_code
        assert "min_size=5" in config.strategy_code
        assert "max_size=50" in config.strategy_code

    def test_unknown_type_strategy(self):
        """Test strategy for unknown attribute type"""
        attr = RequirementAttribute(name="unknown", type=AttributeType.UNKNOWN)
        config = self.generator.generate_strategy(attr)

        assert "st.nothing()" in config.strategy_code

    def test_extract_constraint_ranges_simple(self):
        """Test extracting ranges from simple constraint"""
        ranges = self.generator.extract_constraint_ranges("x >= 10 and x <= 20")

        assert "min" in ranges
        assert "max" in ranges
        assert ranges["min"] == 10.0
        assert ranges["max"] == 20.0

    def test_extract_constraint_ranges_reverse_order(self):
        """Test extracting ranges with reverse comparison"""
        ranges = self.generator.extract_constraint_ranges("150 <= height and height <= 200")

        assert ranges["min"] == 150.0
        assert ranges["max"] == 200.0

    def test_extract_constraint_ranges_only_min(self):
        """Test extracting only minimum range"""
        ranges = self.generator.extract_constraint_ranges("value >= 0")

        assert "min" in ranges
        assert ranges["min"] == 0.0
        assert "max" not in ranges

    def test_extract_constraint_ranges_only_max(self):
        """Test extracting only maximum range"""
        ranges = self.generator.extract_constraint_ranges("value <= 100")

        assert "max" in ranges
        assert ranges["max"] == 100.0
        assert "min" not in ranges

    def test_extract_constraint_ranges_float_values(self):
        """Test extracting float ranges"""
        ranges = self.generator.extract_constraint_ranges("temp >= -10.5 and temp <= 50.5")

        assert ranges["min"] == -10.5
        assert ranges["max"] == 50.5

    def test_generate_composite_strategy(self):
        """Test generating strategies for multiple attributes"""
        attributes = [
            RequirementAttribute(name="x", type=AttributeType.INTEGER),
            RequirementAttribute(name="y", type=AttributeType.REAL),
            RequirementAttribute(name="active", type=AttributeType.BOOLEAN),
        ]

        strategies = self.generator.generate_composite_strategy(attributes)

        assert len(strategies) == 3
        assert "x" in strategies
        assert "y" in strategies
        assert "active" in strategies
        assert "st.integers()" in strategies["x"].strategy_code
        assert "st.floats(" in strategies["y"].strategy_code
        assert "st.booleans()" in strategies["active"].strategy_code

    def test_generate_composite_strategy_with_ranges(self):
        """Test generating composite strategy with constraint ranges"""
        attributes = [
            RequirementAttribute(name="x", type=AttributeType.INTEGER),
            RequirementAttribute(name="y", type=AttributeType.REAL),
        ]

        constraint_ranges = {
            "x": {"min": 0, "max": 100},
            "y": {"min": -10.0, "max": 10.0},
        }

        strategies = self.generator.generate_composite_strategy(attributes, constraint_ranges)

        assert "min_value=0" in strategies["x"].strategy_code
        assert "max_value=100" in strategies["x"].strategy_code
        assert "min_value=-10.0" in strategies["y"].strategy_code
        assert "max_value=10.0" in strategies["y"].strategy_code

    def test_base_imports(self):
        """Test that base imports are included"""
        attr = RequirementAttribute(name="x", type=AttributeType.INTEGER)
        config = self.generator.generate_strategy(attr)

        assert len(config.imports) > 0
        assert any("strategies as st" in imp or "from hypothesis" in imp for imp in config.imports)

    def test_strategy_attribute_precedence(self):
        """Test that attribute bounds take precedence over constraint ranges"""
        attr = RequirementAttribute(
            name="x",
            type=AttributeType.INTEGER,
            min_value=50,
            max_value=150,
        )

        # Constraint ranges suggest different bounds
        ranges = {"min": 0, "max": 200}

        config = self.generator.generate_strategy(attr, ranges)

        # Attribute bounds should be used
        assert "min_value=50" in config.strategy_code
        assert "max_value=150" in config.strategy_code
