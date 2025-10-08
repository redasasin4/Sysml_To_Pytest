#!/usr/bin/env python3
"""
Demo: End-to-end workflow for SysML V2 to pytest integration

This script demonstrates:
1. Parsing SysML V2 requirement models (simulated)
2. Extracting requirements
3. Generating pytest tests with Hypothesis
4. Running tests with traceability

Note: This uses mock data since we don't have a running SysML V2 API server
"""

from pathlib import Path

# Now import from the sysml2pytest package
from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    AttributeType,
)
from sysml2pytest.generator import PytestGenerator, GeneratorConfig


def create_sample_requirements():
    """
    Create sample requirements (simulating extraction from SysML V2 model)

    In production, these would be extracted via:
        client = SysMLV2Client(api_url="http://localhost:9000")
        extractor = RequirementExtractor(client)
        requirements = extractor.extract_requirements(project_id="my-project")
    """
    requirements = []

    # REQ-001: Tree Height Requirement
    req1 = Requirement(
        metadata=RequirementMetadata(
            id="REQ-001",
            name="TreeHeightRequirement",
            qualified_name="ChristmasTreeRequirements::TreeHeightRequirement",
            documentation="The Christmas tree shall be at least 150 cm and maximum 200 cm high.",
            subject="tree",
        ),
        attributes=[
            RequirementAttribute(
                name="treeHeight",
                type=AttributeType.INTEGER,
                description="Height of the tree in centimeters",
            )
        ],
        constraints=[
            Constraint(
                kind=ConstraintKind.REQUIRE,
                expression="150 <= treeHeight and treeHeight <= 200",
                description="Height must be between 150 and 200 cm",
            )
        ],
    )
    requirements.append(req1)

    # REQ-002: Ornament Count Requirement
    req2 = Requirement(
        metadata=RequirementMetadata(
            id="REQ-002",
            name="OrnamentCountRequirement",
            qualified_name="ChristmasTreeRequirements::OrnamentCountRequirement",
            documentation="The Christmas tree shall have between 20 and 100 ornaments for proper decoration.",
            subject="tree",
        ),
        attributes=[
            RequirementAttribute(
                name="ornamentCount",
                type=AttributeType.INTEGER,
            )
        ],
        constraints=[
            Constraint(
                kind=ConstraintKind.REQUIRE,
                expression="ornamentCount >= 20 and ornamentCount <= 100",
            )
        ],
    )
    requirements.append(req2)

    # REQ-003: Lights Power Requirement
    req3 = Requirement(
        metadata=RequirementMetadata(
            id="REQ-003",
            name="LightsPowerRequirement",
            qualified_name="ChristmasTreeRequirements::LightsPowerRequirement",
            documentation="The Christmas tree lights shall consume no more than 500 watts to ensure safety.",
            subject="lights",
        ),
        attributes=[
            RequirementAttribute(
                name="powerConsumption",
                type=AttributeType.REAL,
            )
        ],
        constraints=[
            Constraint(
                kind=ConstraintKind.ASSUME,
                expression="powerConsumption >= 0",
            ),
            Constraint(
                kind=ConstraintKind.REQUIRE,
                expression="powerConsumption <= 500.0",
            ),
        ],
    )
    requirements.append(req3)

    # REQ-004: Tree Stability Requirement
    req4 = Requirement(
        metadata=RequirementMetadata(
            id="REQ-004",
            name="TreeStabilityRequirement",
            qualified_name="ChristmasTreeRequirements::TreeStabilityRequirement",
            documentation="The tree base diameter shall be at least 15% of the tree height for stability.",
            subject="tree",
        ),
        attributes=[
            RequirementAttribute(name="treeHeight", type=AttributeType.REAL),
            RequirementAttribute(name="baseDiameter", type=AttributeType.REAL),
        ],
        constraints=[
            Constraint(
                kind=ConstraintKind.ASSUME,
                expression="treeHeight > 0 and baseDiameter > 0",
            ),
            Constraint(
                kind=ConstraintKind.REQUIRE,
                expression="baseDiameter >= 0.15 * treeHeight",
            ),
        ],
    )
    requirements.append(req4)

    return requirements


def main():
    """Run the demo workflow"""
    print("=" * 70)
    print("SysML V2 to Pytest Integration - Demo Workflow")
    print("=" * 70)

    # Step 1: Create/extract requirements
    print("\n[1/3] Extracting requirements from SysML V2 model...")
    requirements = create_sample_requirements()
    print(f"      ✓ Extracted {len(requirements)} requirements")

    for req in requirements:
        print(f"        - {req.metadata.id}: {req.metadata.name}")

    # Step 2: Generate pytest tests
    print("\n[2/3] Generating pytest tests with Hypothesis...")

    config = GeneratorConfig(
        output_dir=Path(__file__).parent / "tests",
        system_module="examples.system.christmas_tree",
        use_hypothesis=True,
        format_code=False,  # Skip formatting for demo (black may not be installed)
        custom_imports=[
            "from examples.system.christmas_tree import (",
            "    validate_tree_height,",
            "    validate_ornament_count,",
            "    validate_lights_power,",
            "    validate_tree_stability,",
            ")",
        ],
    )

    generator = PytestGenerator(config)
    output_file = generator.generate_tests(requirements)

    print(f"      ✓ Generated test file: {output_file}")

    # Step 3: Show generated test preview
    print("\n[3/3] Generated test preview:")
    print("      " + "-" * 60)

    with open(output_file, "r") as f:
        lines = f.readlines()
        # Show first 50 lines
        for i, line in enumerate(lines[:50]):
            print(f"      {line.rstrip()}")

        if len(lines) > 50:
            print(f"      ... ({len(lines) - 50} more lines)")

    print("      " + "-" * 60)

    # Instructions
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nTo run the generated tests:")
    print(f"  cd {Path(__file__).parent}")
    print(f"  pytest {output_file.name} -v --requirement-summary")
    print("\nTo generate traceability report:")
    print(f"  pytest {output_file.name} --requirement-trace=trace.json")
    print(f"  pytest {output_file.name} --requirement-trace-md=trace.md")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
