/**
 * Example SysML V2 Requirements for Christmas Tree System
 * Demonstrates property-based requirements with constraints
 */

package ChristmasTreeRequirements {

    import ScalarValues::*;

    /**
     * REQ-001: Tree Height Requirement
     * The Christmas tree shall have a height between 150 and 200 cm
     */
    requirement def TreeHeightRequirement {
        doc /* The Christmas tree shall be at least 150 cm and maximum 200 cm high. */

        subject tree : ChristmasTree;

        attribute treeHeight : Integer;

        require constraint {
            150 <= treeHeight and treeHeight <= 200
        }
    }

    /**
     * REQ-002: Ornament Count Requirement
     * The tree shall have between 20 and 100 ornaments
     */
    requirement def OrnamentCountRequirement {
        doc /* The Christmas tree shall have between 20 and 100 ornaments for proper decoration. */

        subject tree : ChristmasTree;

        attribute ornamentCount : Integer;

        require constraint {
            ornamentCount >= 20 and ornamentCount <= 100
        }
    }

    /**
     * REQ-003: Lights Power Consumption
     * The lights shall consume no more than 500 watts
     */
    requirement def LightsPowerRequirement {
        doc /* The Christmas tree lights shall consume no more than 500 watts to ensure safety. */

        subject lights : ChristmasLights;

        attribute powerConsumption : Real;

        assume constraint {
            powerConsumption >= 0
        }

        require constraint {
            powerConsumption <= 500.0
        }
    }

    /**
     * REQ-004: Tree Stability Requirement
     * Base diameter must be proportional to tree height
     */
    requirement def TreeStabilityRequirement {
        doc /* The tree base diameter shall be at least 15% of the tree height for stability. */

        subject tree : ChristmasTree;

        attribute treeHeight : Real;
        attribute baseDiameter : Real;

        assume constraint {
            treeHeight > 0 and baseDiameter > 0
        }

        require constraint {
            baseDiameter >= 0.15 * treeHeight
        }
    }

    /**
     * REQ-005: Temperature Safety Requirement
     * Lights shall not exceed safe operating temperature
     */
    requirement def TemperatureSafetyRequirement {
        doc /* The lights operating temperature shall remain below 80 degrees Celsius. */

        subject lights : ChristmasLights;

        attribute operatingTemp : Real;
        attribute ambientTemp : Real;

        assume constraint {
            ambientTemp >= -20.0 and ambientTemp <= 40.0
        }

        require constraint {
            operatingTemp < 80.0
        }
    }

    /**
     * REQ-006: Color Distribution Requirement
     * Ornaments should have diverse colors
     */
    requirement def ColorDistributionRequirement {
        doc /* At least 3 different ornament colors shall be present. */

        subject tree : ChristmasTree;

        attribute uniqueColors : Integer;

        require constraint {
            uniqueColors >= 3
        }
    }

    /**
     * REQ-007: Composite Requirement - Full Tree Validation
     * Combines multiple sub-requirements
     */
    requirement def CompleteTreeRequirement {
        doc /* The complete Christmas tree system shall satisfy all component requirements. */

        subject tree : ChristmasTree;

        // Nested requirements
        require TreeHeightRequirement;
        require OrnamentCountRequirement;
        require ColorDistributionRequirement;
        require TreeStabilityRequirement;
    }
}
