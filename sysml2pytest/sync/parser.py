"""
Test file parser

Parses existing pytest test files to extract metadata and protected regions
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TestMetadata:
    """Metadata extracted from test file"""
    requirement_id: str
    requirement_name: str
    content_hash: str
    version: int
    generated_at: str
    generator_version: str

    @classmethod
    def from_comment_block(cls, lines: List[str]) -> Optional["TestMetadata"]:
        """Parse metadata from comment block"""
        metadata = {}

        for line in lines:
            line = line.strip()
            if not line.startswith("#"):
                continue

            # Parse key: value format
            if ":" in line:
                key_value = line[1:].strip()  # Remove #
                if ":" in key_value:
                    key, value = key_value.split(":", 1)
                    metadata[key.strip()] = value.strip()

        if "requirement_id" not in metadata:
            return None

        return cls(
            requirement_id=metadata.get("requirement_id", ""),
            requirement_name=metadata.get("requirement_name", ""),
            content_hash=metadata.get("content_hash", ""),
            version=int(metadata.get("version", 1)),
            generated_at=metadata.get("generated_at", ""),
            generator_version=metadata.get("generator_version", ""),
        )


@dataclass
class ProtectedRegion:
    """A protected (custom) code region"""
    region_type: str  # "GENERATED" or "CUSTOM"
    start_line: int
    end_line: int
    content: List[str] = field(default_factory=list)

    def get_content_str(self) -> str:
        """Get content as string"""
        return "\n".join(self.content)


@dataclass
class ParsedTest:
    """A parsed test function"""
    function_name: str
    metadata: Optional[TestMetadata]
    start_line: int
    end_line: int
    generated_regions: List[ProtectedRegion] = field(default_factory=list)
    custom_regions: List[ProtectedRegion] = field(default_factory=list)
    full_content: List[str] = field(default_factory=list)

    def has_custom_code(self) -> bool:
        """Check if test has any custom code"""
        for region in self.custom_regions:
            # Check if region has non-comment, non-empty lines
            for line in region.content:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return True
        return False

    def get_custom_code(self) -> List[str]:
        """Get all custom code lines"""
        custom_lines = []
        for region in self.custom_regions:
            custom_lines.extend(region.content)
        return custom_lines


class TestFileParser:
    """Parses pytest test files to extract metadata and regions"""

    # Markers for regions
    METADATA_START = "# SYSML2PYTEST-METADATA-START"
    METADATA_END = "# SYSML2PYTEST-METADATA-END"
    GENERATED_START = "# SYSML2PYTEST-GENERATED-START"
    GENERATED_END = "# SYSML2PYTEST-GENERATED-END"
    CUSTOM_START = "# SYSML2PYTEST-CUSTOM-START"
    CUSTOM_END = "# SYSML2PYTEST-CUSTOM-END"

    def __init__(self):
        """Initialize parser"""
        pass

    def parse_file(self, file_path: Path) -> List[ParsedTest]:
        """
        Parse a test file and extract all tests

        Args:
            file_path: Path to test file

        Returns:
            List of ParsedTest objects
        """
        if not file_path.exists():
            logger.error(f"Test file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            tests = self._parse_tests(lines)
            logger.info(f"Parsed {len(tests)} tests from {file_path}")
            return tests

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

    def _parse_tests(self, lines: List[str]) -> List[ParsedTest]:
        """Parse all tests from file content"""
        tests = []
        i = 0

        while i < len(lines):
            # Look for metadata start
            if lines[i].strip() == self.METADATA_START:
                test = self._parse_single_test(lines, i)
                if test:
                    tests.append(test)
                    i = test.end_line + 1
                else:
                    i += 1
            else:
                i += 1

        return tests

    def _parse_single_test(self, lines: List[str], start_idx: int) -> Optional[ParsedTest]:
        """Parse a single test starting at metadata block"""
        try:
            # Parse metadata
            metadata_lines, metadata_end = self._extract_block(
                lines, start_idx, self.METADATA_START, self.METADATA_END
            )
            metadata = TestMetadata.from_comment_block(metadata_lines)

            if not metadata:
                logger.warning(f"Could not parse metadata at line {start_idx}")
                return None

            # Find test function name
            func_name, func_line = self._find_test_function(lines, metadata_end)
            if not func_name:
                logger.warning(f"Could not find test function for {metadata.requirement_id}")
                return None

            # Find end of test (next metadata block or end of file)
            test_end = self._find_test_end(lines, metadata_end)

            # Extract all regions
            generated_regions = []
            custom_regions = []

            current = metadata_end
            while current < test_end:
                if lines[current].strip() == self.GENERATED_START:
                    content, end = self._extract_block(
                        lines, current, self.GENERATED_START, self.GENERATED_END
                    )
                    generated_regions.append(ProtectedRegion(
                        region_type="GENERATED",
                        start_line=current,
                        end_line=end,
                        content=content
                    ))
                    current = end + 1

                elif lines[current].strip() == self.CUSTOM_START:
                    content, end = self._extract_block(
                        lines, current, self.CUSTOM_START, self.CUSTOM_END
                    )
                    custom_regions.append(ProtectedRegion(
                        region_type="CUSTOM",
                        start_line=current,
                        end_line=end,
                        content=content
                    ))
                    current = end + 1
                else:
                    current += 1

            # Get full test content
            full_content = lines[start_idx:test_end + 1]

            return ParsedTest(
                function_name=func_name,
                metadata=metadata,
                start_line=start_idx,
                end_line=test_end,
                generated_regions=generated_regions,
                custom_regions=custom_regions,
                full_content=full_content
            )

        except Exception as e:
            logger.error(f"Error parsing test at line {start_idx}: {e}")
            return None

    def _extract_block(
        self,
        lines: List[str],
        start_idx: int,
        start_marker: str,
        end_marker: str
    ) -> Tuple[List[str], int]:
        """Extract content between markers"""
        content = []
        i = start_idx + 1  # Skip start marker

        while i < len(lines):
            if lines[i].strip() == end_marker:
                return content, i

            content.append(lines[i].rstrip())
            i += 1

        # End marker not found, return what we have
        return content, len(lines) - 1

    def _find_test_function(self, lines: List[str], start_idx: int) -> Tuple[Optional[str], int]:
        """Find test function definition"""
        func_pattern = re.compile(r'def\s+(test_\w+)\s*\(')

        for i in range(start_idx, min(start_idx + 20, len(lines))):
            match = func_pattern.search(lines[i])
            if match:
                return match.group(1), i

        return None, -1

    def _find_test_end(self, lines: List[str], start_idx: int) -> int:
        """Find end of test (next metadata block or end of file)"""
        for i in range(start_idx, len(lines)):
            if lines[i].strip() == self.METADATA_START:
                return i - 1

        return len(lines) - 1

    def extract_requirement_ids(self, file_path: Path) -> List[str]:
        """Extract all requirement IDs from a test file"""
        tests = self.parse_file(file_path)
        return [test.metadata.requirement_id for test in tests if test.metadata]

    def has_custom_code(self, file_path: Path) -> bool:
        """Check if file has any custom code"""
        tests = self.parse_file(file_path)
        return any(test.has_custom_code() for test in tests)

    def get_test_by_requirement_id(
        self,
        file_path: Path,
        requirement_id: str
    ) -> Optional[ParsedTest]:
        """Get test for a specific requirement ID"""
        tests = self.parse_file(file_path)
        for test in tests:
            if test.metadata and test.metadata.requirement_id == requirement_id:
                return test
        return None
