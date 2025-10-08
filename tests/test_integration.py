"""
Integration tests for full workflow
"""

import pytest
import json
from pathlib import Path

from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    AttributeType,
)
from sysml2pytest.extractor import RequirementExtractor
from sysml2pytest.generator import PytestGenerator, GeneratorConfig
from sysml2pytest.transpiler import ConstraintTranspiler, HypothesisStrategyGenerator


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""

    def test_requirement_json_serialization_roundtrip(self, sample_simple_requirement):
        """Test requirement can be saved and loaded from JSON"""
        # Convert to dict
        req_dict = sample_simple_requirement.to_dict()

        # Reconstruct from dict
        reconstructed = Requirement.from_dict(req_dict)

        # Verify all fields match
        assert reconstructed.metadata.id == sample_simple_requirement.metadata.id
        assert reconstructed.metadata.name == sample_simple_requirement.metadata.name
        assert len(reconstructed.attributes) == len(sample_simple_requirement.attributes)
        assert len(reconstructed.constraints) == len(sample_simple_requirement.constraints)

    def test_save_and_load_requirements(self, tmp_path, sample_simple_requirement, sample_complex_requirement):
        """Test saving and loading multiple requirements"""
        requirements = [sample_simple_requirement, sample_complex_requirement]
        output_file = tmp_path / "requirements.json"

        # Save
        extractor = RequirementExtractor(None)  # No client needed for save/load
        extractor.save_requirements(requirements, output_file)

        assert output_file.exists()

        # Load
        loaded_requirements = RequirementExtractor.load_requirements(output_file)

        assert len(loaded_requirements) == len(requirements)
        assert loaded_requirements[0].metadata.id == requirements[0].metadata.id
        assert loaded_requirements[1].metadata.id == requirements[1].metadata.id

    def test_full_workflow_extract_save_load_generate(self, tmp_path):
        """Test full workflow: create requirements, save, load, generate tests"""
        # Step 1: Create sample requirements
        requirements = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-INT-001",
                    name="IntegrationTestRequirement",
                    qualified_name="Integration::IntegrationTestRequirement",
                    documentation="Test requirement for integration testing",
                ),
                attributes=[
                    RequirementAttribute(name="value", type=AttributeType.INTEGER)
                ],
                constraints=[
                    Constraint(
                        kind=ConstraintKind.REQUIRE,
                        expression="value >= 0 and value <= 100",
                    )
                ],
            )
        ]

        # Step 2: Save to JSON
        req_file = tmp_path / "requirements.json"
        extractor = RequirementExtractor(None)
        extractor.save_requirements(requirements, req_file)

        # Step 3: Load from JSON
        loaded_requirements = RequirementExtractor.load_requirements(req_file)
        assert len(loaded_requirements) == 1

        # Step 4: Generate pytest tests
        config = GeneratorConfig(
            output_dir=tmp_path / "tests",
            format_code=False,
        )
        generator = PytestGenerator(config)
        output_file = generator.generate_tests(loaded_requirements)

        # Step 5: Verify generated test file
        assert output_file.exists()
        content = output_file.read_text()

        assert "@pytest.mark.requirement" in content
        assert 'id="REQ-INT-001"' in content
        assert "def test_" in content


@pytest.mark.integration
class TestTranspilerGeneratorIntegration:
    """Test integration between transpiler and generator"""

    def test_constraint_transpilation_in_generated_tests(self, tmp_path):
        """Test that constraints are correctly transpiled in generated tests"""
        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-TRANS-001",
                name="TranspilerTestReq",
                qualified_name="Test::TranspilerTestReq",
            ),
            attributes=[
                RequirementAttribute(name="x", type=AttributeType.INTEGER),
                RequirementAttribute(name="y", type=AttributeType.INTEGER),
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.ASSUME,
                    expression="x >= 0",
                ),
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="x + y <= 100",
                ),
            ],
        )

        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([requirement])

        content = output_file.read_text()

        # Check that assume constraint is present
        assert "assume(" in content
        assert "x >= 0" in content

        # Check that require constraint is present as assertion
        assert "assert" in content

    def test_hypothesis_strategy_in_generated_tests(self, tmp_path):
        """Test that Hypothesis strategies are correctly generated"""
        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-HYP-001",
                name="HypothesisTestReq",
                qualified_name="Test::HypothesisTestReq",
            ),
            attributes=[
                RequirementAttribute(
                    name="temperature",
                    type=AttributeType.REAL,
                ),
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="temperature >= -10.0 and temperature <= 50.0",
                ),
            ],
        )

        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([requirement])

        content = output_file.read_text()

        # Check for Hypothesis decorators and strategies
        assert "@given(" in content
        assert "st.floats(" in content
        assert "temperature" in content


@pytest.mark.integration
class TestGeneratedTestExecution:
    """Test that generated tests can actually be executed"""

    def test_generated_test_is_valid_python(self, tmp_path, sample_simple_requirement):
        """Test that generated test file is valid Python syntax"""
        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([sample_simple_requirement])

        # Try to compile the generated code
        content = output_file.read_text()
        try:
            compile(content, str(output_file), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated test has syntax error: {e}")

    def test_generated_test_structure(self, tmp_path):
        """Test that generated test has correct structure"""
        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-STRUCT-001",
                name="StructureTestReq",
                qualified_name="Test::StructureTestReq",
                documentation="Test requirement structure",
            ),
            attributes=[
                RequirementAttribute(name="count", type=AttributeType.INTEGER),
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="count >= 1 and count <= 10",
                ),
            ],
        )

        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([requirement])

        content = output_file.read_text()

        # Verify test structure
        assert "import pytest" in content
        assert "from hypothesis import" in content
        assert "@pytest.mark.requirement" in content
        assert "@given(" in content
        assert "def test_" in content
        assert '"""' in content  # Docstring
        assert "assert" in content


@pytest.mark.integration
class TestComplexRequirements:
    """Test handling of complex requirements"""

    def test_multiple_attributes_and_constraints(self, tmp_path):
        """Test requirement with multiple attributes and complex constraints"""
        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-COMPLEX-001",
                name="ComplexRequirement",
                qualified_name="Test::ComplexRequirement",
            ),
            attributes=[
                RequirementAttribute(name="width", type=AttributeType.REAL),
                RequirementAttribute(name="height", type=AttributeType.REAL),
                RequirementAttribute(name="depth", type=AttributeType.REAL),
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.ASSUME,
                    expression="width > 0 and height > 0 and depth > 0",
                ),
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="width * height * depth <= 1000",
                ),
            ],
        )

        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([requirement])

        content = output_file.read_text()

        # Verify all attributes are in strategy
        assert "width" in content
        assert "height" in content
        assert "depth" in content

        # Verify constraints
        assert "assume(" in content
        assert "assert" in content

    def test_implies_operator_in_constraint(self, tmp_path):
        """Test requirement with implies operator in constraint"""
        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-IMPLIES-001",
                name="ImpliesRequirement",
                qualified_name="Test::ImpliesRequirement",
            ),
            attributes=[
                RequirementAttribute(name="voltage", type=AttributeType.REAL),
                RequirementAttribute(name="charging", type=AttributeType.BOOLEAN),
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="voltage > 4.25 implies not charging",
                ),
            ],
        )

        config = GeneratorConfig(output_dir=tmp_path, format_code=False)
        generator = PytestGenerator(config)
        output_file = generator.generate_tests([requirement])

        content = output_file.read_text()

        # Implies should be transpiled to (not A) or B
        assert "assert" in content
        assert "voltage" in content
        assert "charging" in content


@pytest.mark.integration
class TestJSONCompatibility:
    """Test JSON serialization/deserialization compatibility"""

    def test_json_file_format(self, tmp_path, sample_simple_requirement):
        """Test JSON file format is correct"""
        requirements = [sample_simple_requirement]
        output_file = tmp_path / "test_requirements.json"

        extractor = RequirementExtractor(None)
        extractor.save_requirements(requirements, output_file)

        # Load and parse JSON
        with open(output_file, 'r') as f:
            data = json.load(f)

        # Verify structure
        assert "requirements" in data
        assert "count" in data
        assert data["count"] == 1
        assert len(data["requirements"]) == 1

        # Verify requirement structure
        req_data = data["requirements"][0]
        assert "metadata" in req_data
        assert "attributes" in req_data
        assert "constraints" in req_data

    def test_attribute_type_serialization(self, tmp_path):
        """Test that attribute types serialize correctly"""
        requirements = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-TYPES-001",
                    name="TypesTestReq",
                    qualified_name="Test::TypesTestReq",
                ),
                attributes=[
                    RequirementAttribute(name="int_attr", type=AttributeType.INTEGER),
                    RequirementAttribute(name="real_attr", type=AttributeType.REAL),
                    RequirementAttribute(name="bool_attr", type=AttributeType.BOOLEAN),
                    RequirementAttribute(name="str_attr", type=AttributeType.STRING),
                ],
            )
        ]

        output_file = tmp_path / "types_test.json"
        extractor = RequirementExtractor(None)
        extractor.save_requirements(requirements, output_file)

        # Load back
        loaded = RequirementExtractor.load_requirements(output_file)

        # Verify types preserved
        assert loaded[0].attributes[0].type == AttributeType.INTEGER
        assert loaded[0].attributes[1].type == AttributeType.REAL
        assert loaded[0].attributes[2].type == AttributeType.BOOLEAN
        assert loaded[0].attributes[3].type == AttributeType.STRING
