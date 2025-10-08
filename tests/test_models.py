"""
Unit tests for data models
"""

import pytest
from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    AttributeType,
)


class TestRequirementAttribute:
    """Test RequirementAttribute model"""

    def test_create_integer_attribute(self):
        """Test creating integer attribute"""
        attr = RequirementAttribute(
            name="count",
            type=AttributeType.INTEGER,
            description="Item count",
            min_value=0,
            max_value=100,
        )
        assert attr.name == "count"
        assert attr.type == AttributeType.INTEGER
        assert attr.min_value == 0
        assert attr.max_value == 100

    def test_create_real_attribute(self):
        """Test creating real attribute"""
        attr = RequirementAttribute(
            name="temperature",
            type=AttributeType.REAL,
            min_value=-10.5,
            max_value=50.5,
        )
        assert attr.type == AttributeType.REAL
        assert attr.min_value == -10.5
        assert attr.max_value == 50.5

    def test_create_boolean_attribute(self):
        """Test creating boolean attribute"""
        attr = RequirementAttribute(
            name="isActive",
            type=AttributeType.BOOLEAN,
        )
        assert attr.type == AttributeType.BOOLEAN

    def test_create_string_attribute(self):
        """Test creating string attribute"""
        attr = RequirementAttribute(
            name="deviceName",
            type=AttributeType.STRING,
        )
        assert attr.type == AttributeType.STRING

    def test_attribute_to_dict(self):
        """Test converting attribute to dictionary"""
        attr = RequirementAttribute(
            name="count",
            type=AttributeType.INTEGER,
            description="Item count",
        )
        data = attr.to_dict()
        assert data["name"] == "count"
        assert data["type"] == "Integer"
        assert data["description"] == "Item count"


class TestConstraint:
    """Test Constraint model"""

    def test_create_assume_constraint(self):
        """Test creating assume constraint"""
        constraint = Constraint(
            kind=ConstraintKind.ASSUME,
            expression="x >= 0",
            description="x must be non-negative",
        )
        assert constraint.kind == ConstraintKind.ASSUME
        assert constraint.expression == "x >= 0"

    def test_create_require_constraint(self):
        """Test creating require constraint"""
        constraint = Constraint(
            kind=ConstraintKind.REQUIRE,
            expression="x <= 100",
        )
        assert constraint.kind == ConstraintKind.REQUIRE
        assert constraint.expression == "x <= 100"

    def test_constraint_to_dict(self):
        """Test converting constraint to dictionary"""
        constraint = Constraint(
            kind=ConstraintKind.REQUIRE,
            expression="x >= 10",
            description="Lower bound",
        )
        data = constraint.to_dict()
        assert data["kind"] == "require"
        assert data["expression"] == "x >= 10"
        assert data["description"] == "Lower bound"


class TestRequirementMetadata:
    """Test RequirementMetadata model"""

    def test_create_metadata(self):
        """Test creating requirement metadata"""
        metadata = RequirementMetadata(
            id="REQ-001",
            name="TestRequirement",
            qualified_name="Package::TestRequirement",
            documentation="This is a test requirement",
            subject="system",
        )
        assert metadata.id == "REQ-001"
        assert metadata.name == "TestRequirement"
        assert metadata.qualified_name == "Package::TestRequirement"
        assert metadata.documentation == "This is a test requirement"
        assert metadata.subject == "system"

    def test_metadata_with_stakeholders(self):
        """Test metadata with stakeholders"""
        metadata = RequirementMetadata(
            id="REQ-002",
            name="StakeholderRequirement",
            qualified_name="Package::StakeholderRequirement",
            stakeholders=["Alice", "Bob"],
            actors=["User", "Admin"],
        )
        assert len(metadata.stakeholders) == 2
        assert "Alice" in metadata.stakeholders
        assert len(metadata.actors) == 2
        assert "User" in metadata.actors

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = RequirementMetadata(
            id="REQ-003",
            name="DictRequirement",
            qualified_name="Package::DictRequirement",
        )
        data = metadata.to_dict()
        assert data["id"] == "REQ-003"
        assert data["name"] == "DictRequirement"


class TestRequirement:
    """Test Requirement model"""

    def test_create_simple_requirement(self, sample_requirement_metadata, sample_integer_attribute, sample_constraint_require):
        """Test creating simple requirement"""
        req = Requirement(
            metadata=sample_requirement_metadata,
            attributes=[sample_integer_attribute],
            constraints=[sample_constraint_require],
        )
        assert req.metadata.id == "REQ-001"
        assert len(req.attributes) == 1
        assert len(req.constraints) == 1

    def test_requirement_with_multiple_constraints(self, sample_requirement_metadata, sample_integer_attribute):
        """Test requirement with multiple constraints"""
        constraints = [
            Constraint(kind=ConstraintKind.ASSUME, expression="x >= 0"),
            Constraint(kind=ConstraintKind.REQUIRE, expression="x <= 100"),
        ]
        req = Requirement(
            metadata=sample_requirement_metadata,
            attributes=[sample_integer_attribute],
            constraints=constraints,
        )
        assert len(req.constraints) == 2

    def test_assume_constraints_property(self, sample_complex_requirement):
        """Test filtering assume constraints"""
        assume_constraints = sample_complex_requirement.assume_constraints
        assert len(assume_constraints) == 1
        assert assume_constraints[0].kind == ConstraintKind.ASSUME

    def test_require_constraints_property(self, sample_complex_requirement):
        """Test filtering require constraints"""
        require_constraints = sample_complex_requirement.require_constraints
        assert len(require_constraints) == 1
        assert require_constraints[0].kind == ConstraintKind.REQUIRE

    def test_get_attribute_by_name(self, sample_complex_requirement):
        """Test getting attribute by name"""
        attr = sample_complex_requirement.get_attribute("treeHeight")
        assert attr is not None
        assert attr.name == "treeHeight"

    def test_get_nonexistent_attribute(self, sample_simple_requirement):
        """Test getting nonexistent attribute returns None"""
        attr = sample_simple_requirement.get_attribute("nonexistent")
        assert attr is None

    def test_requirement_to_dict(self, sample_simple_requirement):
        """Test converting requirement to dictionary"""
        data = sample_simple_requirement.to_dict()
        assert "metadata" in data
        assert "attributes" in data
        assert "constraints" in data
        assert data["metadata"]["id"] == "REQ-001"

    def test_requirement_from_dict(self, sample_simple_requirement):
        """Test creating requirement from dictionary"""
        data = sample_simple_requirement.to_dict()
        reconstructed = Requirement.from_dict(data)
        assert reconstructed.metadata.id == sample_simple_requirement.metadata.id
        assert reconstructed.metadata.name == sample_simple_requirement.metadata.name
        assert len(reconstructed.attributes) == len(sample_simple_requirement.attributes)
        assert len(reconstructed.constraints) == len(sample_simple_requirement.constraints)

    def test_requirement_with_nested_requirements(self, sample_requirement_metadata):
        """Test requirement with nested requirements"""
        req = Requirement(
            metadata=sample_requirement_metadata,
            nested_requirements=["SUB-REQ-001", "SUB-REQ-002"],
        )
        assert len(req.nested_requirements) == 2
        assert "SUB-REQ-001" in req.nested_requirements

    def test_empty_requirement(self):
        """Test creating requirement with minimal data"""
        metadata = RequirementMetadata(
            id="REQ-EMPTY",
            name="EmptyRequirement",
            qualified_name="Package::EmptyRequirement",
        )
        req = Requirement(metadata=metadata)
        assert len(req.attributes) == 0
        assert len(req.constraints) == 0
        assert len(req.nested_requirements) == 0


class TestAttributeType:
    """Test AttributeType enum"""

    def test_attribute_types(self):
        """Test all attribute types"""
        assert AttributeType.INTEGER.value == "Integer"
        assert AttributeType.REAL.value == "Real"
        assert AttributeType.BOOLEAN.value == "Boolean"
        assert AttributeType.STRING.value == "String"
        assert AttributeType.UNKNOWN.value == "Unknown"


class TestConstraintKind:
    """Test ConstraintKind enum"""

    def test_constraint_kinds(self):
        """Test constraint kinds"""
        assert ConstraintKind.ASSUME.value == "assume"
        assert ConstraintKind.REQUIRE.value == "require"
