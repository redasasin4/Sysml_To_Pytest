"""
Example system under test: Christmas Tree System

This module demonstrates a system that should satisfy
the SysML V2 requirements defined in christmas_tree_requirements.sysml
"""

from typing import List
from dataclasses import dataclass


@dataclass
class ChristmasTree:
    """Christmas tree system"""
    tree_height: float  # cm
    base_diameter: float  # cm
    ornament_count: int
    ornament_colors: List[str]

    def validate_height(self) -> bool:
        """Validate tree height meets requirements (150-200 cm)"""
        return 150 <= self.tree_height <= 200

    def validate_ornaments(self) -> bool:
        """Validate ornament count meets requirements (20-100)"""
        return 20 <= self.ornament_count <= 100

    def validate_color_diversity(self) -> bool:
        """Validate at least 3 different colors"""
        unique_colors = len(set(self.ornament_colors))
        return unique_colors >= 3

    def validate_stability(self) -> bool:
        """Validate base diameter is at least 15% of height"""
        if self.tree_height <= 0:
            return False
        return self.base_diameter >= 0.15 * self.tree_height

    def is_valid(self) -> bool:
        """Check if tree meets all requirements"""
        return (
            self.validate_height()
            and self.validate_ornaments()
            and self.validate_color_diversity()
            and self.validate_stability()
        )


@dataclass
class ChristmasLights:
    """Christmas tree lights system"""
    power_consumption: float  # watts
    operating_temp: float  # celsius
    ambient_temp: float  # celsius

    def validate_power(self) -> bool:
        """Validate power consumption <= 500W"""
        return self.power_consumption >= 0 and self.power_consumption <= 500.0

    def validate_temperature(self) -> bool:
        """Validate operating temperature < 80C"""
        return self.operating_temp < 80.0

    def validate_ambient_range(self) -> bool:
        """Validate ambient temperature in expected range"""
        return -20.0 <= self.ambient_temp <= 40.0

    def is_safe(self) -> bool:
        """Check if lights meet safety requirements"""
        return (
            self.validate_power()
            and self.validate_temperature()
            and self.validate_ambient_range()
        )


# Validation functions for use in generated tests
def validate_tree_height(tree_height: float) -> bool:
    """Validate tree height constraint"""
    return 150 <= tree_height <= 200


def validate_ornament_count(ornament_count: int) -> bool:
    """Validate ornament count constraint"""
    return ornament_count >= 20 and ornament_count <= 100


def validate_lights_power(power_consumption: float) -> bool:
    """Validate lights power consumption constraint"""
    return power_consumption >= 0 and power_consumption <= 500.0


def validate_tree_stability(tree_height: float, base_diameter: float) -> bool:
    """Validate tree stability constraint"""
    if tree_height <= 0 or base_diameter <= 0:
        return False
    return base_diameter >= 0.15 * tree_height


def validate_temperature_safety(operating_temp: float, ambient_temp: float) -> bool:
    """Validate temperature safety constraint"""
    if not (-20.0 <= ambient_temp <= 40.0):
        return False
    return operating_temp < 80.0


def validate_color_diversity(unique_colors: int) -> bool:
    """Validate color diversity constraint"""
    return unique_colors >= 3
