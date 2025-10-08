"""
Generate Hypothesis testing strategies from SysML V2 requirement attributes
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..extractor.models import RequirementAttribute, AttributeType

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """Configuration for generating a Hypothesis strategy"""
    strategy_code: str
    imports: List[str]
    description: str


class HypothesisStrategyGenerator:
    """
    Generates Hypothesis strategies from requirement attributes

    Maps SysML V2 attribute types and constraints to appropriate
    Hypothesis strategies for property-based testing.
    """

    def __init__(self):
        """Initialize strategy generator"""
        self.base_imports = ["from hypothesis import strategies as st"]

    def generate_strategy(
        self,
        attribute: RequirementAttribute,
        constraint_ranges: Optional[Dict[str, Any]] = None
    ) -> StrategyConfig:
        """
        Generate Hypothesis strategy for an attribute

        Args:
            attribute: Requirement attribute
            constraint_ranges: Optional dict with 'min' and 'max' values from constraints

        Returns:
            StrategyConfig with strategy code and required imports
        """
        if attribute.type == AttributeType.INTEGER:
            return self._generate_integer_strategy(attribute, constraint_ranges)
        elif attribute.type == AttributeType.REAL:
            return self._generate_real_strategy(attribute, constraint_ranges)
        elif attribute.type == AttributeType.BOOLEAN:
            return self._generate_boolean_strategy(attribute)
        elif attribute.type == AttributeType.STRING:
            return self._generate_string_strategy(attribute, constraint_ranges)
        else:
            return self._generate_default_strategy(attribute)

    def _generate_integer_strategy(
        self,
        attribute: RequirementAttribute,
        constraint_ranges: Optional[Dict[str, Any]] = None
    ) -> StrategyConfig:
        """Generate strategy for integer attributes"""
        min_val = None
        max_val = None

        # Get bounds from attribute or constraint ranges
        if attribute.min_value is not None:
            min_val = int(attribute.min_value)
        elif constraint_ranges and "min" in constraint_ranges:
            min_val = int(constraint_ranges["min"])

        if attribute.max_value is not None:
            max_val = int(attribute.max_value)
        elif constraint_ranges and "max" in constraint_ranges:
            max_val = int(constraint_ranges["max"])

        # Build strategy
        parts = []
        if min_val is not None:
            parts.append(f"min_value={min_val}")
        if max_val is not None:
            parts.append(f"max_value={max_val}")

        if parts:
            strategy = f"st.integers({', '.join(parts)})"
            desc = f"Integers in range [{min_val or '-∞'}, {max_val or '∞'}]"
        else:
            strategy = "st.integers()"
            desc = "Integers (unbounded)"

        return StrategyConfig(
            strategy_code=strategy,
            imports=self.base_imports.copy(),
            description=desc
        )

    def _generate_real_strategy(
        self,
        attribute: RequirementAttribute,
        constraint_ranges: Optional[Dict[str, Any]] = None
    ) -> StrategyConfig:
        """Generate strategy for real/float attributes"""
        min_val = None
        max_val = None

        if attribute.min_value is not None:
            min_val = float(attribute.min_value)
        elif constraint_ranges and "min" in constraint_ranges:
            min_val = float(constraint_ranges["min"])

        if attribute.max_value is not None:
            max_val = float(attribute.max_value)
        elif constraint_ranges and "max" in constraint_ranges:
            max_val = float(constraint_ranges["max"])

        parts = []
        if min_val is not None:
            parts.append(f"min_value={min_val}")
        if max_val is not None:
            parts.append(f"max_value={max_val}")

        # Add allow_nan=False, allow_infinity=False for safety
        parts.append("allow_nan=False")
        parts.append("allow_infinity=False")

        strategy = f"st.floats({', '.join(parts)})"
        desc = f"Floats in range [{min_val or '-∞'}, {max_val or '∞'}]"

        return StrategyConfig(
            strategy_code=strategy,
            imports=self.base_imports.copy(),
            description=desc
        )

    def _generate_boolean_strategy(
        self,
        attribute: RequirementAttribute
    ) -> StrategyConfig:
        """Generate strategy for boolean attributes"""
        return StrategyConfig(
            strategy_code="st.booleans()",
            imports=self.base_imports.copy(),
            description="Boolean values (True/False)"
        )

    def _generate_string_strategy(
        self,
        attribute: RequirementAttribute,
        constraint_ranges: Optional[Dict[str, Any]] = None
    ) -> StrategyConfig:
        """Generate strategy for string attributes"""
        min_size = 0
        max_size = None

        if constraint_ranges:
            min_size = constraint_ranges.get("min_length", min_size)
            max_size = constraint_ranges.get("max_length", max_size)

        parts = []
        if min_size > 0:
            parts.append(f"min_size={min_size}")
        if max_size is not None:
            parts.append(f"max_size={max_size}")

        if parts:
            strategy = f"st.text({', '.join(parts)})"
        else:
            strategy = "st.text()"

        desc = f"Text strings (length {min_size}-{max_size or '∞'})"

        return StrategyConfig(
            strategy_code=strategy,
            imports=self.base_imports.copy(),
            description=desc
        )

    def _generate_default_strategy(
        self,
        attribute: RequirementAttribute
    ) -> StrategyConfig:
        """Generate default strategy for unknown types"""
        logger.warning(f"Unknown attribute type {attribute.type}, using st.nothing()")
        return StrategyConfig(
            strategy_code="st.nothing()",
            imports=self.base_imports.copy(),
            description="No strategy (unknown type)"
        )

    def generate_composite_strategy(
        self,
        attributes: List[RequirementAttribute],
        constraint_ranges: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, StrategyConfig]:
        """
        Generate strategies for multiple attributes

        Args:
            attributes: List of requirement attributes
            constraint_ranges: Optional dict mapping attr names to constraint ranges

        Returns:
            Dict mapping attribute names to their strategies
        """
        strategies = {}

        for attr in attributes:
            ranges = None
            if constraint_ranges and attr.name in constraint_ranges:
                ranges = constraint_ranges[attr.name]

            strategies[attr.name] = self.generate_strategy(attr, ranges)

        return strategies

    def extract_constraint_ranges(self, constraint_expr: str) -> Dict[str, Any]:
        """
        Extract min/max ranges from constraint expression

        Args:
            constraint_expr: Constraint expression (e.g., "150 <= x and x <= 200")

        Returns:
            Dict with 'min' and/or 'max' keys if found

        Note:
            This is a simplified implementation. Production version should
            use proper expression parsing.
        """
        import re

        ranges = {}

        # Pattern: number <= var or var >= number (includes negative numbers)
        min_pattern = r'(-?\d+\.?\d*)\s*<=\s*(\w+)|(\w+)\s*>=\s*(-?\d+\.?\d*)'
        # Pattern: var <= number or number >= var (includes negative numbers)
        max_pattern = r'(\w+)\s*<=\s*(-?\d+\.?\d*)|(-?\d+\.?\d*)\s*>=\s*(\w+)'

        for match in re.finditer(min_pattern, constraint_expr):
            if match.group(1):
                ranges['min'] = float(match.group(1))
            elif match.group(4):
                ranges['min'] = float(match.group(4))

        for match in re.finditer(max_pattern, constraint_expr):
            if match.group(2):
                ranges['max'] = float(match.group(2))
            elif match.group(3):
                ranges['max'] = float(match.group(3))

        return ranges
