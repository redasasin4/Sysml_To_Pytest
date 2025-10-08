"""
Test file updater

Applies requirement changes to existing test files while preserving custom code
"""

import logging
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

from .parser import TestFileParser, ParsedTest
from .fingerprint import RequirementFingerprint, compute_requirement_hash
from .detector import ChangeSeverity
from ..extractor.models import Requirement
from ..generator.generator import PytestGenerator, GeneratorConfig

logger = logging.getLogger(__name__)


class UpdateStrategy(Enum):
    """Update strategies for syncing tests"""
    FULL_REGEN = "full_regen"  # Delete and regenerate
    SURGICAL = "surgical"      # Parse and update specific sections
    SIDE_BY_SIDE = "side_by_side"  # Generate .new file
    HYBRID = "hybrid"          # Choose based on severity


@dataclass
class UpdateResult:
    """Result of updating a test file"""
    file_path: Path
    success: bool
    strategy_used: UpdateStrategy
    lines_preserved: int = 0
    lines_updated: int = 0
    backup_path: Optional[Path] = None
    error_message: Optional[str] = None
    version_old: int = 0
    version_new: int = 0

    def __str__(self) -> str:
        if not self.success:
            return f"❌ Failed: {self.file_path} - {self.error_message}"

        return (
            f"✓ Updated {self.file_path}\n"
            f"  - Version: {self.version_old} → {self.version_new}\n"
            f"  - Preserved {self.lines_preserved} lines of custom code\n"
            f"  - Updated {self.lines_updated} auto-generated lines\n"
            f"  - Backup: {self.backup_path}"
        )


class TestUpdater:
    """Updates existing test files when requirements change"""

    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        create_backups: bool = True
    ):
        """
        Initialize test updater

        Args:
            backup_dir: Directory for backups (default: .sysml2pytest/backups)
            create_backups: Whether to create backups before updating
        """
        self.parser = TestFileParser()

        # Create generator with minimal config
        config = GeneratorConfig(
            output_dir=Path("."),  # Won't be used
            use_hypothesis=True,
            format_code=False
        )
        self.generator = PytestGenerator(config)
        self.create_backups = create_backups

        if backup_dir:
            self.backup_dir = backup_dir
        else:
            self.backup_dir = Path.cwd() / ".sysml2pytest" / "backups"

    def update_test_file(
        self,
        test_file: Path,
        requirement: Requirement,
        strategy: UpdateStrategy = UpdateStrategy.SURGICAL,
        severity: ChangeSeverity = ChangeSeverity.MODERATE,
        new_version: int = 2
    ) -> UpdateResult:
        """
        Update a test file with changed requirement

        Args:
            test_file: Path to test file
            requirement: Updated requirement
            strategy: Update strategy to use
            severity: Change severity level
            new_version: New version number

        Returns:
            UpdateResult with details of the update
        """
        try:
            # Choose strategy based on hybrid mode
            if strategy == UpdateStrategy.HYBRID:
                strategy = self._choose_strategy(severity)
                logger.info(f"Hybrid mode: using {strategy.value} for severity {severity.value}")

            # Execute strategy
            if strategy == UpdateStrategy.FULL_REGEN:
                return self._full_regeneration(test_file, requirement, new_version)
            elif strategy == UpdateStrategy.SURGICAL:
                return self._surgical_update(test_file, requirement, new_version)
            elif strategy == UpdateStrategy.SIDE_BY_SIDE:
                return self._side_by_side_update(test_file, requirement, new_version)
            else:
                return UpdateResult(
                    file_path=test_file,
                    success=False,
                    strategy_used=strategy,
                    error_message=f"Unknown strategy: {strategy}"
                )

        except Exception as e:
            logger.error(f"Failed to update {test_file}: {e}")
            return UpdateResult(
                file_path=test_file,
                success=False,
                strategy_used=strategy,
                error_message=str(e)
            )

    def _choose_strategy(self, severity: ChangeSeverity) -> UpdateStrategy:
        """Choose update strategy based on change severity"""
        if severity == ChangeSeverity.NONE:
            return UpdateStrategy.SURGICAL
        elif severity == ChangeSeverity.MINOR:
            return UpdateStrategy.SURGICAL
        elif severity == ChangeSeverity.MODERATE:
            return UpdateStrategy.SURGICAL
        else:  # MAJOR
            return UpdateStrategy.SIDE_BY_SIDE

    def _create_backup(self, test_file: Path) -> Optional[Path]:
        """Create backup of test file"""
        if not self.create_backups:
            return None

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            backup_name = f"{test_file.name}.backup.{timestamp}"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(test_file, backup_path)
            logger.info(f"Created backup: {backup_path}")

            return backup_path

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            return None

    def _full_regeneration(
        self,
        test_file: Path,
        requirement: Requirement,
        new_version: int
    ) -> UpdateResult:
        """
        Full regeneration strategy - deletes and regenerates test file

        WARNING: This loses ALL custom code!
        """
        logger.warning(f"Full regeneration will lose custom code in {test_file}")

        # Create backup
        backup_path = self._create_backup(test_file)

        # Parse old file to get version
        old_tests = self.parser.parse_file(test_file)
        old_version = old_tests[0].metadata.version if old_tests and old_tests[0].metadata else 1

        # Generate new test
        test_code = self.generator._generate_test_for_requirement(requirement)

        # Update version and metadata in generated code
        content_hash = compute_requirement_hash(requirement)
        test_code = self._update_metadata_in_code(test_code, content_hash, new_version)

        # Write new file
        with open(test_file, 'w') as f:
            f.write(test_code)

        lines_updated = len(test_code.splitlines())

        return UpdateResult(
            file_path=test_file,
            success=True,
            strategy_used=UpdateStrategy.FULL_REGEN,
            lines_preserved=0,
            lines_updated=lines_updated,
            backup_path=backup_path,
            version_old=old_version,
            version_new=new_version
        )

    def _surgical_update(
        self,
        test_file: Path,
        requirement: Requirement,
        new_version: int
    ) -> UpdateResult:
        """
        Surgical update strategy - updates generated sections, preserves custom code
        """
        # Create backup
        backup_path = self._create_backup(test_file)

        # Parse existing test file
        parsed_tests = self.parser.parse_file(test_file)

        if not parsed_tests:
            logger.error(f"No tests found in {test_file}")
            return UpdateResult(
                file_path=test_file,
                success=False,
                strategy_used=UpdateStrategy.SURGICAL,
                error_message="No tests found in file"
            )

        # Find test matching requirement
        requirement_id = requirement.metadata.id or requirement.metadata.name
        target_test = None
        for test in parsed_tests:
            if test.metadata and test.metadata.requirement_id == requirement_id:
                target_test = test
                break

        if not target_test:
            logger.error(f"Test for requirement {requirement_id} not found in {test_file}")
            return UpdateResult(
                file_path=test_file,
                success=False,
                strategy_used=UpdateStrategy.SURGICAL,
                error_message=f"Test for {requirement_id} not found"
            )

        old_version = target_test.metadata.version if target_test.metadata else 1

        # Generate new test code
        new_test_code = self.generator._generate_test_for_requirement(requirement)

        # Update version and hash in new code
        content_hash = compute_requirement_hash(requirement)
        new_test_code = self._update_metadata_in_code(
            new_test_code,
            content_hash,
            new_version
        )

        # Merge: Replace old test with new, preserving custom code
        merged_code = self._merge_test_code(target_test, new_test_code)

        # Read full file
        with open(test_file, 'r') as f:
            full_content = f.read()

        # Replace old test with merged version
        # Extract old test content
        old_test_lines = full_content.splitlines()
        old_test_content = '\n'.join(old_test_lines[target_test.start_line:target_test.end_line + 1])

        updated_content = full_content.replace(old_test_content, merged_code)

        # Write updated file
        with open(test_file, 'w') as f:
            f.write(updated_content)

        # Count preserved custom lines
        custom_line_count = sum(len(region.content) for region in target_test.custom_regions)
        updated_line_count = len(merged_code.splitlines())

        return UpdateResult(
            file_path=test_file,
            success=True,
            strategy_used=UpdateStrategy.SURGICAL,
            lines_preserved=custom_line_count,
            lines_updated=updated_line_count,
            backup_path=backup_path,
            version_old=old_version,
            version_new=new_version
        )

    def _side_by_side_update(
        self,
        test_file: Path,
        requirement: Requirement,
        new_version: int
    ) -> UpdateResult:
        """
        Side-by-side strategy - generates .new file for manual review
        """
        # No backup needed - original file unchanged

        # Parse old file to get version
        old_tests = self.parser.parse_file(test_file)
        old_version = old_tests[0].metadata.version if old_tests and old_tests[0].metadata else 1

        # Generate new test
        test_code = self.generator._generate_test_for_requirement(requirement)

        # Update version and metadata in generated code
        content_hash = compute_requirement_hash(requirement)
        test_code = self._update_metadata_in_code(test_code, content_hash, new_version)

        # Write .new file
        new_file_path = test_file.with_suffix(test_file.suffix + '.new')
        with open(new_file_path, 'w') as f:
            f.write(test_code)

        lines_updated = len(test_code.splitlines())

        return UpdateResult(
            file_path=new_file_path,
            success=True,
            strategy_used=UpdateStrategy.SIDE_BY_SIDE,
            lines_preserved=0,
            lines_updated=lines_updated,
            backup_path=None,
            version_old=old_version,
            version_new=new_version
        )

    def _merge_test_code(self, old_test: ParsedTest, new_code: str) -> str:
        """
        Merge new generated code with old custom code regions

        Args:
            old_test: Parsed old test with custom regions
            new_code: Newly generated test code

        Returns:
            Merged test code with custom regions preserved
        """
        # Parse new code to identify insertion points for custom code
        new_lines = new_code.splitlines()

        # Find CUSTOM region markers in new code
        custom_region_indices = []
        for i, line in enumerate(new_lines):
            if line.strip() == self.parser.CUSTOM_START:
                custom_region_indices.append(i)

        # If we have custom code from old test, insert it
        if old_test.custom_regions and custom_region_indices:
            # Take the first custom region from old test
            old_custom_content = old_test.custom_regions[0].content

            # Insert after CUSTOM_START marker
            insert_idx = custom_region_indices[0] + 1

            # Remove placeholder comment in new code
            # Find CUSTOM_END
            custom_end_idx = -1
            for i in range(insert_idx, len(new_lines)):
                if new_lines[i].strip() == self.parser.CUSTOM_END:
                    custom_end_idx = i
                    break

            if custom_end_idx > insert_idx:
                # Remove lines between CUSTOM_START and CUSTOM_END
                new_lines = new_lines[:insert_idx] + new_lines[custom_end_idx:]

                # Insert old custom code
                for i, custom_line in enumerate(old_custom_content):
                    new_lines.insert(insert_idx + i, custom_line)

        return '\n'.join(new_lines)

    def _update_version_in_code(self, code: str, version: int) -> str:
        """Update version number in test code"""
        lines = code.splitlines()
        updated_lines = []

        for line in lines:
            if line.startswith("# version:"):
                updated_lines.append(f"# version: {version}")
            elif "@pytest.mark.requirement(" in line and "version=" in line:
                # Update version in decorator
                import re
                line = re.sub(r'version=\d+', f'version={version}', line)
                updated_lines.append(line)
            else:
                updated_lines.append(line)

        return '\n'.join(updated_lines)

    def _update_metadata_in_code(
        self,
        code: str,
        content_hash: str,
        version: int
    ) -> str:
        """Update metadata (hash, version) in test code"""
        lines = code.splitlines()
        updated_lines = []

        for line in lines:
            if line.startswith("# content_hash:"):
                updated_lines.append(f"# content_hash: {content_hash}")
            elif line.startswith("# version:"):
                updated_lines.append(f"# version: {version}")
            elif line.startswith("# generated_at:"):
                timestamp = datetime.now().isoformat()
                updated_lines.append(f"# generated_at: {timestamp}")
            elif "@pytest.mark.requirement(" in line and "version=" in line:
                # Update version in decorator
                import re
                line = re.sub(r'version=\d+', f'version={version}', line)
                updated_lines.append(line)
            else:
                updated_lines.append(line)

        return '\n'.join(updated_lines)

    def update_multiple_tests(
        self,
        updates: List[Dict],
        strategy: UpdateStrategy = UpdateStrategy.SURGICAL
    ) -> List[UpdateResult]:
        """
        Update multiple test files

        Args:
            updates: List of dicts with keys: test_file, requirement, severity, new_version
            strategy: Update strategy to use

        Returns:
            List of UpdateResult objects
        """
        results = []

        for update_spec in updates:
            result = self.update_test_file(
                test_file=update_spec['test_file'],
                requirement=update_spec['requirement'],
                strategy=strategy,
                severity=update_spec.get('severity', ChangeSeverity.MODERATE),
                new_version=update_spec.get('new_version', 2)
            )
            results.append(result)

            if result.success:
                logger.info(f"✓ Updated {result.file_path}")
            else:
                logger.error(f"✗ Failed to update {result.file_path}: {result.error_message}")

        return results

    def print_update_summary(self, results: List[UpdateResult]):
        """Print summary of update results"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        total_preserved = sum(r.lines_preserved for r in results if r.success)
        total_updated = sum(r.lines_updated for r in results if r.success)

        print("=" * 70)
        print("Test Update Summary")
        print("=" * 70)
        print(f"Total files: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Custom code preserved: {total_preserved} lines")
        print(f"Generated code updated: {total_updated} lines")
        print("=" * 70)

        if failed > 0:
            print("\nFailed updates:")
            for result in results:
                if not result.success:
                    print(f"  - {result.file_path}: {result.error_message}")
