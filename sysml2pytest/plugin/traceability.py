"""
Requirements traceability tracking and reporting
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .markers import RequirementMarker

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    test_file: str
    outcome: str  # passed, failed, skipped, error
    duration: float
    error_message: Optional[str] = None


@dataclass
class RequirementTrace:
    """Traceability information for a requirement"""
    requirement_id: str
    requirement_name: Optional[str]
    tests: List[TestResult] = field(default_factory=list)

    @property
    def test_count(self) -> int:
        return len(self.tests)

    @property
    def passed_count(self) -> int:
        return sum(1 for t in self.tests if t.outcome == "passed")

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tests if t.outcome == "failed")

    @property
    def skipped_count(self) -> int:
        return sum(1 for t in self.tests if t.outcome == "skipped")

    @property
    def is_verified(self) -> bool:
        """Requirement is verified if all tests pass"""
        return self.test_count > 0 and self.failed_count == 0

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "requirement_id": self.requirement_id,
            "requirement_name": self.requirement_name,
            "test_count": self.test_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count,
            "verified": self.is_verified,
            "tests": [
                {
                    "name": t.test_name,
                    "file": t.test_file,
                    "outcome": t.outcome,
                    "duration": t.duration,
                    "error": t.error_message,
                }
                for t in self.tests
            ],
        }


class TraceabilityCollector:
    """
    Collects traceability data during pytest execution

    Hooks into pytest's collection and execution phases to track
    which tests verify which requirements.
    """

    def __init__(self):
        """Initialize collector"""
        self.requirements: Dict[str, RequirementTrace] = {}
        self.untested_requirements: Set[str] = set()
        self.tests_without_requirements: List[str] = []

    def register_requirement(self, req_id: str, req_name: Optional[str] = None):
        """Register a requirement from the model"""
        if req_id not in self.requirements:
            self.requirements[req_id] = RequirementTrace(
                requirement_id=req_id,
                requirement_name=req_name
            )
            self.untested_requirements.add(req_id)

    def record_test(
        self,
        requirement_marker: RequirementMarker,
        test_name: str,
        test_file: str,
        outcome: str,
        duration: float,
        error_message: Optional[str] = None
    ):
        """Record a test result"""
        req_id = requirement_marker.id

        # Ensure requirement exists
        if req_id not in self.requirements:
            self.requirements[req_id] = RequirementTrace(
                requirement_id=req_id,
                requirement_name=requirement_marker.name
            )

        # Remove from untested set
        self.untested_requirements.discard(req_id)

        # Add test result
        test_result = TestResult(
            test_name=test_name,
            test_file=test_file,
            outcome=outcome,
            duration=duration,
            error_message=error_message
        )
        self.requirements[req_id].tests.append(test_result)

    def record_test_without_requirement(self, test_name: str):
        """Record a test that doesn't have a requirement marker"""
        self.tests_without_requirements.append(test_name)

    def generate_report(self) -> "TraceabilityReport":
        """Generate traceability report"""
        return TraceabilityReport(
            requirements=list(self.requirements.values()),
            untested_requirements=list(self.untested_requirements),
            tests_without_requirements=self.tests_without_requirements
        )


@dataclass
class TraceabilityReport:
    """Complete traceability report"""
    requirements: List[RequirementTrace]
    untested_requirements: List[str] = field(default_factory=list)
    tests_without_requirements: List[str] = field(default_factory=list)

    @property
    def total_requirements(self) -> int:
        return len(self.requirements) + len(self.untested_requirements)

    @property
    def tested_requirements(self) -> int:
        return len(self.requirements)

    @property
    def verified_requirements(self) -> int:
        return sum(1 for req in self.requirements if req.is_verified)

    @property
    def coverage_percentage(self) -> float:
        """Percentage of requirements with tests"""
        if self.total_requirements == 0:
            return 0.0
        return (self.tested_requirements / self.total_requirements) * 100

    @property
    def verification_percentage(self) -> float:
        """Percentage of requirements verified (all tests pass)"""
        if self.total_requirements == 0:
            return 0.0
        return (self.verified_requirements / self.total_requirements) * 100

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "summary": {
                "total_requirements": self.total_requirements,
                "tested_requirements": self.tested_requirements,
                "verified_requirements": self.verified_requirements,
                "coverage_percentage": self.coverage_percentage,
                "verification_percentage": self.verification_percentage,
            },
            "requirements": [req.to_dict() for req in self.requirements],
            "untested_requirements": self.untested_requirements,
            "tests_without_requirements": self.tests_without_requirements,
        }

    def save_json(self, output_file: Path):
        """Save report as JSON"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved traceability report to {output_file}")

    def save_markdown(self, output_file: Path):
        """Save report as Markdown"""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("# Requirements Traceability Report\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Requirements**: {self.total_requirements}\n")
            f.write(f"- **Requirements with Tests**: {self.tested_requirements}\n")
            f.write(f"- **Verified Requirements**: {self.verified_requirements}\n")
            f.write(f"- **Coverage**: {self.coverage_percentage:.1f}%\n")
            f.write(f"- **Verification**: {self.verification_percentage:.1f}%\n\n")

            # Requirements table
            f.write("## Requirements Details\n\n")
            f.write("| Requirement ID | Name | Tests | Passed | Failed | Verified |\n")
            f.write("|----------------|------|-------|--------|--------|----------|\n")

            for req in sorted(self.requirements, key=lambda r: r.requirement_id):
                status = "✓" if req.is_verified else "✗"
                f.write(
                    f"| {req.requirement_id} | {req.requirement_name or 'N/A'} | "
                    f"{req.test_count} | {req.passed_count} | {req.failed_count} | {status} |\n"
                )

            # Untested requirements
            if self.untested_requirements:
                f.write("\n## Untested Requirements\n\n")
                for req_id in sorted(self.untested_requirements):
                    f.write(f"- {req_id}\n")

            # Tests without requirements
            if self.tests_without_requirements:
                f.write("\n## Tests Without Requirements\n\n")
                for test_name in sorted(self.tests_without_requirements):
                    f.write(f"- {test_name}\n")

        logger.info(f"Saved traceability report to {output_file}")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 60)
        print("Requirements Traceability Summary")
        print("=" * 60)
        print(f"Total Requirements:      {self.total_requirements}")
        print(f"Requirements with Tests: {self.tested_requirements}")
        print(f"Verified Requirements:   {self.verified_requirements}")
        print(f"Coverage:                {self.coverage_percentage:.1f}%")
        print(f"Verification:            {self.verification_percentage:.1f}%")

        if self.untested_requirements:
            print(f"\nUntested Requirements:   {len(self.untested_requirements)}")

        if self.tests_without_requirements:
            print(f"Tests Without Req:       {len(self.tests_without_requirements)}")

        print("=" * 60 + "\n")
