/**
 * Example SysML V2 Requirements for Battery System
 * Demonstrates complex property-based requirements with multiple constraints
 */

package BatterySystemRequirements {

    import ScalarValues::*;

    /**
     * REQ-BAT-001: Battery Capacity Requirement
     */
    requirement def BatteryCapacityRequirement {
        doc /* The battery shall have a capacity between 2000 and 5000 mAh. */

        subject battery : Battery;

        attribute capacity : Real;

        require constraint {
            capacity >= 2000.0 and capacity <= 5000.0
        }
    }

    /**
     * REQ-BAT-002: Voltage Range Requirement
     */
    requirement def VoltageRangeRequirement {
        doc /* The battery voltage shall be maintained between 3.0V and 4.2V during operation. */

        subject battery : Battery;

        attribute voltage : Real;

        require constraint {
            voltage >= 3.0 and voltage <= 4.2
        }
    }

    /**
     * REQ-BAT-003: Charge Rate Requirement
     */
    requirement def ChargeRateRequirement {
        doc /* The battery charge rate shall not exceed 1C (capacity in mAh). */

        subject battery : Battery;

        attribute chargeRate : Real;
        attribute capacity : Real;

        assume constraint {
            capacity > 0
        }

        require constraint {
            chargeRate <= capacity
        }
    }

    /**
     * REQ-BAT-004: Discharge Efficiency Requirement
     */
    requirement def DischargeEfficiencyRequirement {
        doc /* The battery discharge efficiency shall be at least 85%. */

        subject battery : Battery;

        attribute efficiency : Real;

        assume constraint {
            efficiency >= 0.0 and efficiency <= 1.0
        }

        require constraint {
            efficiency >= 0.85
        }
    }

    /**
     * REQ-BAT-005: Temperature Operating Range
     */
    requirement def TemperatureOperatingRequirement {
        doc /* The battery shall operate safely between -10°C and 50°C. */

        subject battery : Battery;

        attribute temperature : Real;

        require constraint {
            temperature >= -10.0 and temperature <= 50.0
        }
    }

    /**
     * REQ-BAT-006: Cycle Life Requirement
     */
    requirement def CycleLifeRequirement {
        doc /* The battery shall maintain 80% capacity after 500 charge cycles. */

        subject battery : Battery;

        attribute cycleCount : Integer;
        attribute capacityRetention : Real;

        assume constraint {
            cycleCount >= 0 and capacityRetention >= 0.0 and capacityRetention <= 1.0
        }

        require constraint {
            cycleCount <= 500 or capacityRetention >= 0.80
        }
    }

    /**
     * REQ-BAT-007: State of Charge Accuracy
     */
    requirement def StateOfChargeAccuracyRequirement {
        doc /* The state of charge measurement shall have an accuracy within ±5%. */

        subject battery : Battery;

        attribute measuredSoC : Real;
        attribute actualSoC : Real;

        assume constraint {
            measuredSoC >= 0.0 and measuredSoC <= 1.0 and
            actualSoC >= 0.0 and actualSoC <= 1.0
        }

        require constraint {
            (measuredSoC - actualSoC) >= -0.05 and
            (measuredSoC - actualSoC) <= 0.05
        }
    }

    /**
     * REQ-BAT-008: Power Delivery Requirement
     */
    requirement def PowerDeliveryRequirement {
        doc /* The battery shall deliver at least 10W of power continuously. */

        subject battery : Battery;

        attribute voltage : Real;
        attribute current : Real;
        attribute power : Real;

        assume constraint {
            voltage > 0 and current >= 0
        }

        require constraint {
            power >= 10.0 and power == voltage * current
        }
    }

    /**
     * REQ-BAT-009: Safety Cutoff Requirement
     */
    requirement def SafetyCutoffRequirement {
        doc /* The battery shall cut off charging when voltage exceeds 4.25V or temperature exceeds 55°C. */

        subject battery : Battery;

        attribute voltage : Real;
        attribute temperature : Real;
        attribute chargingEnabled : Boolean;

        require constraint {
            (voltage > 4.25 or temperature > 55.0) implies not chargingEnabled
        }
    }

    /**
     * REQ-BAT-010: Complete Battery System Requirement
     */
    requirement def CompleteBatterySystemRequirement {
        doc /* The complete battery system shall satisfy all safety and performance requirements. */

        subject battery : Battery;

        require BatteryCapacityRequirement;
        require VoltageRangeRequirement;
        require TemperatureOperatingRequirement;
        require DischargeEfficiencyRequirement;
        require SafetyCutoffRequirement;
    }
}
