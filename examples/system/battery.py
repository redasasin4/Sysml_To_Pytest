"""
Example system under test: Battery System

This module demonstrates a system that should satisfy
the SysML V2 requirements defined in battery_requirements.sysml
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Battery:
    """Battery system"""
    capacity: float  # mAh
    voltage: float  # V
    temperature: float  # celsius
    charge_rate: float  # mAh
    cycle_count: int
    capacity_retention: float  # 0.0-1.0
    charging_enabled: bool = True

    def validate_capacity(self) -> bool:
        """Validate capacity is in range 2000-5000 mAh"""
        return 2000.0 <= self.capacity <= 5000.0

    def validate_voltage(self) -> bool:
        """Validate voltage is in operating range 3.0-4.2V"""
        return 3.0 <= self.voltage <= 4.2

    def validate_charge_rate(self) -> bool:
        """Validate charge rate does not exceed 1C (capacity)"""
        return self.charge_rate <= self.capacity

    def validate_efficiency(self) -> bool:
        """Validate discharge efficiency >= 85%"""
        return 0.85 <= self.capacity_retention <= 1.0

    def validate_temperature(self) -> bool:
        """Validate operating temperature -10C to 50C"""
        return -10.0 <= self.temperature <= 50.0

    def validate_cycle_life(self) -> bool:
        """Validate capacity retention after cycles"""
        # After 500 cycles, should maintain 80% capacity
        if self.cycle_count <= 500:
            return True
        return self.capacity_retention >= 0.80

    def validate_safety_cutoff(self) -> bool:
        """Validate safety cutoff logic"""
        # Should disable charging if voltage > 4.25V or temp > 55C
        if self.voltage > 4.25 or self.temperature > 55.0:
            return not self.charging_enabled
        return True

    def is_valid(self) -> bool:
        """Check if battery meets all requirements"""
        return (
            self.validate_capacity()
            and self.validate_voltage()
            and self.validate_charge_rate()
            and self.validate_temperature()
            and self.validate_safety_cutoff()
        )


# Validation functions for generated tests
def validate_battery_capacity(capacity: float) -> bool:
    """REQ-BAT-001: Battery capacity 2000-5000 mAh"""
    return 2000.0 <= capacity <= 5000.0


def validate_voltage_range(voltage: float) -> bool:
    """REQ-BAT-002: Voltage range 3.0-4.2V"""
    return 3.0 <= voltage <= 4.2


def validate_charge_rate_limit(charge_rate: float, capacity: float) -> bool:
    """REQ-BAT-003: Charge rate <= 1C"""
    if capacity <= 0:
        return False
    return charge_rate <= capacity


def validate_discharge_efficiency(efficiency: float) -> bool:
    """REQ-BAT-004: Discharge efficiency >= 85%"""
    if not (0.0 <= efficiency <= 1.0):
        return False
    return efficiency >= 0.85


def validate_temperature_range(temperature: float) -> bool:
    """REQ-BAT-005: Operating temperature -10C to 50C"""
    return -10.0 <= temperature <= 50.0


def validate_cycle_life(cycle_count: int, capacity_retention: float) -> bool:
    """REQ-BAT-006: Maintain 80% capacity after 500 cycles"""
    if not (0.0 <= capacity_retention <= 1.0):
        return False
    if cycle_count > 500:
        return capacity_retention >= 0.80
    return True


def validate_soc_accuracy(measured_soc: float, actual_soc: float) -> bool:
    """REQ-BAT-007: SoC accuracy within ±5%"""
    if not (0.0 <= measured_soc <= 1.0 and 0.0 <= actual_soc <= 1.0):
        return False
    diff = measured_soc - actual_soc
    return -0.05 <= diff <= 0.05


def validate_power_delivery(voltage: float, current: float, power: float) -> bool:
    """REQ-BAT-008: Power delivery >= 10W"""
    if voltage <= 0 or current < 0:
        return False
    expected_power = voltage * current
    return power >= 10.0 and abs(power - expected_power) < 0.01


def validate_safety_cutoff(voltage: float, temperature: float, charging_enabled: bool) -> bool:
    """REQ-BAT-009: Safety cutoff when V>4.25V or T>55C"""
    if voltage > 4.25 or temperature > 55.0:
        return not charging_enabled
    return True
