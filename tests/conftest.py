"""
Pytest configuration and fixtures for tests
"""

import pytest
from pathlib import Path

from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    AttributeType,
)


@pytest.fixture
def sample_integer_attribute():
    """Sample integer attribute"""
    return RequirementAttribute(
        name="treeHeight",
        type=AttributeType.INTEGER,
        description="Height of the tree in centimeters",
        min_value=150,
        max_value=200,
    )


@pytest.fixture
def sample_real_attribute():
    """Sample real attribute"""
    return RequirementAttribute(
        name="temperature",
        type=AttributeType.REAL,
        description="Temperature in Celsius",
        min_value=-10.0,
        max_value=50.0,
    )


@pytest.fixture
def sample_boolean_attribute():
    """Sample boolean attribute"""
    return RequirementAttribute(
        name="isActive",
        type=AttributeType.BOOLEAN,
        description="Whether the system is active",
    )


@pytest.fixture
def sample_string_attribute():
    """Sample string attribute"""
    return RequirementAttribute(
        name="deviceName",
        type=AttributeType.STRING,
        description="Name of the device",
    )


@pytest.fixture
def sample_constraint_assume():
    """Sample assume constraint"""
    return Constraint(
        kind=ConstraintKind.ASSUME,
        expression="temperature > -20",
        description="Temperature must be above absolute minimum",
    )


@pytest.fixture
def sample_constraint_require():
    """Sample require constraint"""
    return Constraint(
        kind=ConstraintKind.REQUIRE,
        expression="150 <= treeHeight and treeHeight <= 200",
        description="Height must be between 150 and 200 cm",
    )


@pytest.fixture
def sample_requirement_metadata():
    """Sample requirement metadata"""
    return RequirementMetadata(
        id="REQ-001",
        name="TreeHeightRequirement",
        qualified_name="ChristmasTreeRequirements::TreeHeightRequirement",
        documentation="The Christmas tree shall be at least 150 cm and maximum 200 cm high.",
        subject="tree",
    )


@pytest.fixture
def sample_simple_requirement(sample_requirement_metadata, sample_integer_attribute, sample_constraint_require):
    """Sample simple requirement with one attribute and one constraint"""
    return Requirement(
        metadata=sample_requirement_metadata,
        attributes=[sample_integer_attribute],
        constraints=[sample_constraint_require],
    )


@pytest.fixture
def sample_complex_requirement():
    """Sample complex requirement with multiple attributes and constraints"""
    metadata = RequirementMetadata(
        id="REQ-004",
        name="TreeStabilityRequirement",
        qualified_name="ChristmasTreeRequirements::TreeStabilityRequirement",
        documentation="The tree base diameter shall be at least 15% of the tree height for stability.",
        subject="tree",
    )

    attributes = [
        RequirementAttribute(name="treeHeight", type=AttributeType.REAL),
        RequirementAttribute(name="baseDiameter", type=AttributeType.REAL),
    ]

    constraints = [
        Constraint(
            kind=ConstraintKind.ASSUME,
            expression="treeHeight > 0 and baseDiameter > 0",
        ),
        Constraint(
            kind=ConstraintKind.REQUIRE,
            expression="baseDiameter >= 0.15 * treeHeight",
        ),
    ]

    return Requirement(
        metadata=metadata,
        attributes=attributes,
        constraints=constraints,
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
