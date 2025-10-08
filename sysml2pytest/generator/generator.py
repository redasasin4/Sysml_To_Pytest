"""
Pytest test generator from SysML V2 requirements
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..extractor.models import Requirement, ConstraintKind
from ..transpiler import ConstraintTranspiler, HypothesisStrategyGenerator
from .templates import TestTemplate

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Configuration for test generator"""
    output_dir: Path
    system_module: str = "system"
    system_function_template: str = "{subject}.{method}({params})"
    use_hypothesis: bool = True
    use_parametrize: bool = False
    include_docstrings: bool = True
    format_code: bool = True
    custom_imports: List[str] = field(default_factory=list)


class PytestGenerator:
    """Generates pytest test files from requirements"""

    def __init__(self, config: GeneratorConfig):
        """
        Initialize generator

        Args:
            config: Generator configuration
        """
        self.config = config
        self.transpiler = ConstraintTranspiler()
        self.strategy_generator = HypothesisStrategyGenerator()
        self.template = TestTemplate()

    def generate_tests(
        self,
        requirements: List[Requirement],
        output_file: Optional[Path] = None
    ) -> Path:
        """
        Generate pytest test file from requirements

        Args:
            requirements: List of requirements to generate tests for
            output_file: Optional specific output file path

        Returns:
            Path to generated test file
        """
        if not requirements:
            raise ValueError("No requirements provided")

        # Determine output file
        if output_file is None:
            output_file = self.config.output_dir / "test_generated_requirements.py"

        # Generate test code
        test_code = self._generate_test_file(requirements)

        # Optionally format code
        if self.config.format_code:
            test_code = self._format_code(test_code)

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(test_code)

        logger.info(f"Generated tests for {len(requirements)} requirements in {output_file}")
        return output_file

    def generate_tests_per_requirement(
        self,
        requirements: List[Requirement]
    ) -> Dict[str, Path]:
        """
        Generate separate test file for each requirement

        Args:
            requirements: List of requirements

        Returns:
            Dict mapping requirement ID to generated file path
        """
        generated_files = {}

        for requirement in requirements:
            filename = f"test_{self._sanitize_name(requirement.metadata.name)}.py"
            output_file = self.config.output_dir / filename

            test_code = self._generate_test_file([requirement])

            if self.config.format_code:
                test_code = self._format_code(test_code)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(test_code)

            generated_files[requirement.metadata.id] = output_file

        logger.info(f"Generated {len(generated_files)} test files")
        return generated_files

    def _generate_test_file(self, requirements: List[Requirement]) -> str:
        """Generate complete test file code"""
        # Header
        header = self.template.render_file_header(
            source_file="SysML V2 Model",
            requirement_count=len(requirements),
            timestamp=datetime.now().isoformat(),
            custom_imports=self.config.custom_imports
        )

        # Generate test functions
        test_functions = []
        for requirement in requirements:
            try:
                test_code = self._generate_test_for_requirement(requirement)
                test_functions.append(test_code)
            except Exception as e:
                logger.error(f"Failed to generate test for {requirement.metadata.name}: {e}")
                # Include error comment in generated file
                test_functions.append(
                    f"\n# ERROR: Could not generate test for {requirement.metadata.name}\n"
                    f"# Reason: {e}\n"
                )

        # Combine all parts
        full_code = header + "\n\n" + "\n\n".join(test_functions)
        return full_code

    def _generate_test_for_requirement(self, requirement: Requirement) -> str:
        """Generate test function for a single requirement"""
        # Check if composite requirement
        if requirement.nested_requirements:
            return self._generate_composite_test(requirement)

        # Property-based test with Hypothesis
        if self.config.use_hypothesis and requirement.attributes:
            return self._generate_property_test(requirement)

        # Simple assertion test
        return self._generate_simple_test(requirement)

    def _generate_property_test(self, requirement: Requirement) -> str:
        """Generate property-based test using Hypothesis"""
        # Generate strategies for each attribute
        strategies = {}
        for attr in requirement.attributes:
            # Try to extract constraint ranges for this attribute
            ranges = self._extract_ranges_for_attribute(attr.name, requirement)
            strategy_config = self.strategy_generator.generate_strategy(attr, ranges)
            strategies[attr.name] = strategy_config.strategy_code

        # Parameter list
        param_list = ", ".join([attr.name for attr in requirement.attributes])

        # Transpile assume constraints
        assume_constraints = []
        assume_code = []
        for constraint in requirement.assume_constraints:
            assume_constraints.append(constraint.expression)
            transpiled = self.transpiler.transpile(constraint.expression)
            assume_code.append(f"assume({transpiled.python_code})")

        # Transpile require constraints
        require_constraints = []
        require_code = []
        for constraint in requirement.require_constraints:
            require_constraints.append(constraint.expression)
            transpiled = self.transpiler.transpile(constraint.expression)
            require_code.append(f"assert {transpiled.python_code}")

        # Generate system call
        system_call = self._generate_system_call(requirement, param_list)

        # Compute content hash for sync tracking
        try:
            from ..sync.fingerprint import compute_requirement_hash
            content_hash = compute_requirement_hash(requirement)
        except ImportError:
            content_hash = ""

        # Render template
        return self.template.render_property_test(
            requirement_id=requirement.metadata.id or requirement.metadata.name,
            requirement_name=requirement.metadata.name,
            test_function_name=self._sanitize_name(requirement.metadata.name),
            documentation=requirement.metadata.documentation or "No documentation",
            strategies=strategies,
            param_list=param_list,
            assume_constraints=assume_constraints,
            require_constraints=require_constraints,
            assume_constraint_code=assume_code,
            require_constraint_code=require_code,
            system_call=system_call,
            content_hash=content_hash,
            version=1,  # Initial version
            generator_version="0.1.0"
        )

    def _generate_simple_test(self, requirement: Requirement) -> str:
        """Generate simple assertion test"""
        test_name = self._sanitize_name(requirement.metadata.name)
        doc = requirement.metadata.documentation or "No documentation"
        req_id = requirement.metadata.id or requirement.metadata.name

        # Combine all require constraints
        assertions = []
        for constraint in requirement.require_constraints:
            transpiled = self.transpiler.transpile(constraint.expression)
            assertions.append(f"assert {transpiled.python_code}")

        constraint_code = "\n    ".join(assertions) if assertions else "pass  # No constraints"

        system_call = "# System call placeholder"

        return self.template.SIMPLE_TEST.render(
            requirement_id=req_id,
            requirement_name=requirement.metadata.name,
            test_function_name=test_name,
            documentation=doc,
            system_call=system_call,
            constraint_code=constraint_code
        )

    def _generate_composite_test(self, requirement: Requirement) -> str:
        """Generate test class for composite requirement"""
        # This would generate a test class with methods for each nested requirement
        # Simplified implementation
        class_name = self._sanitize_name(requirement.metadata.name, capitalize=True)

        return f"""
@pytest.mark.requirement(id="{requirement.metadata.id}", name="{requirement.metadata.name}")
class Test{class_name}:
    \"\"\"
    {requirement.metadata.documentation or 'Composite requirement'}

    Nested requirements: {', '.join(requirement.nested_requirements)}
    \"\"\"
    pass  # Implement nested requirement tests
"""

    def _generate_system_call(self, requirement: Requirement, params: str) -> str:
        """Generate system under test call"""
        subject = requirement.metadata.subject or "system"

        # Simple template: subject.validate(params)
        return f"result = {subject}.validate({params})"

    def _extract_ranges_for_attribute(
        self,
        attr_name: str,
        requirement: Requirement
    ) -> Optional[Dict[str, Any]]:
        """
        Extract min/max ranges for an attribute from constraints

        Args:
            attr_name: Attribute name
            requirement: Requirement containing constraints

        Returns:
            Dict with 'min' and/or 'max' keys if found
        """
        ranges = {}

        # Check all require constraints for this attribute
        for constraint in requirement.require_constraints:
            if attr_name in constraint.expression:
                extracted = self.strategy_generator.extract_constraint_ranges(
                    constraint.expression
                )
                ranges.update(extracted)

        return ranges if ranges else None

    def _sanitize_name(self, name: str, capitalize: bool = False) -> str:
        """
        Sanitize requirement name for Python function/class name

        Args:
            name: Requirement name
            capitalize: Whether to capitalize (for class names)

        Returns:
            Sanitized name
        """
        # Remove non-alphanumeric characters
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Remove leading digits
        sanitized = re.sub(r'^[0-9]+', '', sanitized)

        # Convert to snake_case or PascalCase
        if capitalize:
            # PascalCase
            parts = sanitized.split('_')
            sanitized = ''.join(word.capitalize() for word in parts if word)
        else:
            # snake_case
            sanitized = sanitized.lower()

        # Ensure valid identifier
        if not sanitized:
            sanitized = "unnamed_requirement"

        return sanitized

    def _format_code(self, code: str) -> str:
        """
        Format generated Python code using black

        Args:
            code: Python code to format

        Returns:
            Formatted code
        """
        try:
            import black
            mode = black.FileMode()
            formatted = black.format_str(code, mode=mode)
            return formatted
        except ImportError:
            logger.warning("black not installed, skipping code formatting")
            return code
        except Exception as e:
            logger.warning(f"Failed to format code: {e}")
            return code
