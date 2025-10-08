"""
Unit tests for pytest test generator
"""

import pytest
from pathlib import Path

from sysml2pytest.generator import PytestGenerator, GeneratorConfig
from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    AttributeType,
)


class TestGeneratorConfig:
    """Test GeneratorConfig"""

    def test_default_config(self, temp_output_dir):
        """Test default configuration"""
        config = GeneratorConfig(output_dir=temp_output_dir)

        assert config.output_dir == temp_output_dir
        assert config.system_module == "system"
        assert config.use_hypothesis is True
        assert config.include_docstrings is True

    def test_custom_config(self, temp_output_dir):
        """Test custom configuration"""
        config = GeneratorConfig(
            output_dir=temp_output_dir,
            system_module="my_custom_module",
            use_hypothesis=False,
            format_code=False,
        )

        assert config.system_module == "my_custom_module"
        assert config.use_hypothesis is False
        assert config.format_code is False


class TestPytestGenerator:
    """Test PytestGenerator"""

    def setup_method(self, temp_output_dir=None):
        """Set up test fixtures"""
        # Will be set in each test that needs it
        pass

    def test_generate_tests_basic(self, temp_output_dir, sample_simple_requirement):
        """Test basic test generation"""
        config = GeneratorConfig(
            output_dir=temp_output_dir,
            format_code=False,  # Skip formatting for speed
        )
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])

        assert output_file.exists()
        assert output_file.name == "test_generated_requirements.py"

        # Check file contents
        content = output_file.read_text()
        assert "import pytest" in content
        assert "from hypothesis import" in content
        assert "@pytest.mark.requirement" in content
        assert "def test_" in content

    def test_generate_tests_multiple_requirements(self, temp_output_dir, sample_simple_requirement, sample_complex_requirement):
        """Test generating tests for multiple requirements"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        requirements = [sample_simple_requirement, sample_complex_requirement]
        output_file = generator.generate_tests(requirements)

        content = output_file.read_text()

        # Should have test functions for both requirements
        assert "test_treeheightrequirement" in content.lower() or "TreeHeightRequirement" in content
        assert "test_treestabilityrequirement" in content.lower() or "TreeStabilityRequirement" in content

    def test_generate_tests_custom_output_file(self, temp_output_dir, sample_simple_requirement):
        """Test generating with custom output file name"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        custom_output = temp_output_dir / "test_custom.py"
        output_file = generator.generate_tests([sample_simple_requirement], output_file=custom_output)

        assert output_file == custom_output
        assert output_file.exists()

    def test_generate_tests_with_hypothesis(self, temp_output_dir, sample_simple_requirement):
        """Test generating with Hypothesis enabled"""
        config = GeneratorConfig(
            output_dir=temp_output_dir,
            use_hypothesis=True,
            format_code=False,
        )
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        assert "@given(" in content
        assert "strategies as st" in content

    def test_generate_tests_per_requirement(self, temp_output_dir, sample_simple_requirement, sample_complex_requirement):
        """Test generating separate file per requirement"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        requirements = [sample_simple_requirement, sample_complex_requirement]
        generated_files = generator.generate_tests_per_requirement(requirements)

        assert len(generated_files) == 2
        for req_id, file_path in generated_files.items():
            assert file_path.exists()
            assert file_path.suffix == ".py"
            assert file_path.name.startswith("test_")

    def test_sanitize_name(self, temp_output_dir):
        """Test name sanitization"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        # Test various sanitization scenarios
        assert generator._sanitize_name("SimpleRequirement") == "simplerequirement"
        assert generator._sanitize_name("TreeHeight-Requirement") == "treeheight_requirement"
        assert generator._sanitize_name("123InvalidStart") == "invalidstart"
        assert generator._sanitize_name("With Spaces") == "with_spaces"

    def test_sanitize_name_capitalize(self, temp_output_dir):
        """Test name sanitization with capitalization"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        assert generator._sanitize_name("simple_requirement", capitalize=True) == "SimpleRequirement"
        assert generator._sanitize_name("tree_height", capitalize=True) == "TreeHeight"

    def test_generate_with_assume_constraints(self, temp_output_dir, sample_complex_requirement):
        """Test generating with assume and require constraints"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_complex_requirement])
        content = output_file.read_text()

        assert "assume(" in content
        assert "assert" in content

    def test_generate_with_custom_imports(self, temp_output_dir, sample_simple_requirement):
        """Test generating with custom imports"""
        config = GeneratorConfig(
            output_dir=temp_output_dir,
            format_code=False,
            custom_imports=["from my_module import my_function"],
        )
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        assert "from my_module import my_function" in content

    def test_generate_with_system_module(self, temp_output_dir, sample_simple_requirement):
        """Test generating with custom system module"""
        config = GeneratorConfig(
            output_dir=temp_output_dir,
            system_module="examples.system.christmas_tree",
            format_code=False,
        )
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        # System call should reference the subject
        assert "tree" in content or "system" in content

    def test_empty_requirements_error(self, temp_output_dir):
        """Test that empty requirements list raises error"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        with pytest.raises(ValueError, match="No requirements"):
            generator.generate_tests([])

    def test_generate_file_header(self, temp_output_dir, sample_simple_requirement):
        """Test file header generation"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        # Check header elements
        assert "Auto-generated" in content
        assert "SysML V2" in content
        assert "DO NOT EDIT" in content

    def test_extract_ranges_for_attribute(self, temp_output_dir):
        """Test extracting ranges for attributes from constraints"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        requirement = Requirement(
            metadata=RequirementMetadata(
                id="REQ-TEST",
                name="TestRequirement",
                qualified_name="Test::TestRequirement",
            ),
            attributes=[
                RequirementAttribute(name="value", type=AttributeType.INTEGER)
            ],
            constraints=[
                Constraint(
                    kind=ConstraintKind.REQUIRE,
                    expression="value >= 10 and value <= 100",
                )
            ],
        )

        ranges = generator._extract_ranges_for_attribute("value", requirement)

        assert ranges is not None
        assert "min" in ranges
        assert "max" in ranges


class TestTemplateRendering:
    """Test template rendering"""

    def test_property_test_template(self, temp_output_dir, sample_simple_requirement):
        """Test property-based test template rendering"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        # Check for property test elements
        assert "@pytest.mark.requirement" in content
        assert "@given(" in content
        assert "def test_" in content
        assert '"""' in content  # Docstring

    def test_requirement_marker_format(self, temp_output_dir, sample_simple_requirement):
        """Test requirement marker formatting"""
        config = GeneratorConfig(output_dir=temp_output_dir, format_code=False)
        generator = PytestGenerator(config)

        output_file = generator.generate_tests([sample_simple_requirement])
        content = output_file.read_text()

        # Marker should include ID and name
        assert 'id="REQ-001"' in content
        assert 'name="TreeHeightRequirement"' in content
