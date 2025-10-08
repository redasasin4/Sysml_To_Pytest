"""
Command-line interface for sysml2pytest

Provides commands for:
- Extracting requirements from SysML V2 models
- Generating pytest tests from requirements
- Managing the workflow
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .extractor import SysMLV2Client, RequirementExtractor
from .generator import PytestGenerator, GeneratorConfig
from .sync import (
    SyncDetector,
    SyncStateManager,
    TestUpdater,
    UpdateStrategy,
    TestFileParser,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CLI:
    """Main CLI application"""

    def __init__(self):
        """Initialize CLI"""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog="sysml2pytest",
            description="Convert SysML V2 requirements to pytest tests",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Extract requirements from SysML V2 API
  sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements.json

  # Generate pytest tests from requirements
  sysml2pytest generate -i requirements.json -o tests/ --system-module my_system

  # Full workflow
  sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements.json
  sysml2pytest generate -i requirements.json -o tests/

For more information, visit: https://github.com/yourusername/sysml2pytest
            """
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {__version__}"
        )

        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands"
        )

        # Extract command
        self._add_extract_command(subparsers)

        # Generate command
        self._add_generate_command(subparsers)

        # Workflow command (extract + generate)
        self._add_workflow_command(subparsers)

        # Sync commands
        self._add_sync_status_command(subparsers)
        self._add_sync_command(subparsers)
        self._add_history_command(subparsers)

        return parser

    def _add_extract_command(self, subparsers):
        """Add extract subcommand"""
        extract_parser = subparsers.add_parser(
            "extract",
            help="Extract requirements from SysML V2 model",
            description="Extract requirements from SysML V2 API and save to JSON file"
        )

        extract_parser.add_argument(
            "--api-url",
            required=True,
            help="SysML V2 API Services URL (e.g., http://localhost:9000)"
        )

        extract_parser.add_argument(
            "--project-id",
            required=True,
            help="SysML V2 project identifier"
        )

        extract_parser.add_argument(
            "--commit-id",
            help="Specific commit ID (optional, uses HEAD if not specified)"
        )

        extract_parser.add_argument(
            "--api-token",
            help="API authentication token (optional)"
        )

        extract_parser.add_argument(
            "-o", "--output",
            type=Path,
            default=Path("requirements.json"),
            help="Output JSON file path (default: requirements.json)"
        )

        extract_parser.add_argument(
            "--include-usages",
            action="store_true",
            help="Include requirement usages in addition to definitions"
        )

    def _add_generate_command(self, subparsers):
        """Add generate subcommand"""
        generate_parser = subparsers.add_parser(
            "generate",
            help="Generate pytest tests from requirements",
            description="Generate pytest test files from extracted requirements"
        )

        generate_parser.add_argument(
            "-i", "--input",
            type=Path,
            required=True,
            help="Input requirements JSON file"
        )

        generate_parser.add_argument(
            "-o", "--output-dir",
            type=Path,
            default=Path("tests"),
            help="Output directory for generated tests (default: tests/)"
        )

        generate_parser.add_argument(
            "--output-file",
            type=Path,
            help="Specific output file name (optional, default: test_generated_requirements.py)"
        )

        generate_parser.add_argument(
            "--system-module",
            default="system",
            help="Python module containing system under test (default: system)"
        )

        generate_parser.add_argument(
            "--no-hypothesis",
            action="store_true",
            help="Disable Hypothesis property-based testing"
        )

        generate_parser.add_argument(
            "--no-format",
            action="store_true",
            help="Disable code formatting with black"
        )

        generate_parser.add_argument(
            "--split-files",
            action="store_true",
            help="Generate separate test file for each requirement"
        )

    def _add_workflow_command(self, subparsers):
        """Add workflow subcommand (extract + generate)"""
        workflow_parser = subparsers.add_parser(
            "workflow",
            help="Run full workflow (extract + generate)",
            description="Extract requirements and generate tests in one command"
        )

        workflow_parser.add_argument(
            "--api-url",
            required=True,
            help="SysML V2 API Services URL"
        )

        workflow_parser.add_argument(
            "--project-id",
            required=True,
            help="SysML V2 project identifier"
        )

        workflow_parser.add_argument(
            "--commit-id",
            help="Specific commit ID (optional)"
        )

        workflow_parser.add_argument(
            "--api-token",
            help="API authentication token (optional)"
        )

        workflow_parser.add_argument(
            "-o", "--output-dir",
            type=Path,
            default=Path("tests"),
            help="Output directory for generated tests (default: tests/)"
        )

        workflow_parser.add_argument(
            "--system-module",
            default="system",
            help="Python module containing system under test"
        )

        workflow_parser.add_argument(
            "--requirements-file",
            type=Path,
            default=Path("requirements.json"),
            help="Intermediate requirements JSON file (default: requirements.json)"
        )

    def run(self, args: Optional[list] = None) -> int:
        """
        Run CLI application

        Args:
            args: Command-line arguments (defaults to sys.argv)

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parsed_args = self.parser.parse_args(args)

        # Configure logging level
        if parsed_args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Handle no command
        if not parsed_args.command:
            self.parser.print_help()
            return 1

        # Dispatch to command handler
        try:
            if parsed_args.command == "extract":
                return self._handle_extract(parsed_args)
            elif parsed_args.command == "generate":
                return self._handle_generate(parsed_args)
            elif parsed_args.command == "workflow":
                return self._handle_workflow(parsed_args)
            else:
                logger.error(f"Unknown command: {parsed_args.command}")
                return 1

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=parsed_args.verbose)
            return 1

    def _handle_extract(self, args) -> int:
        """Handle extract command"""
        logger.info("=" * 70)
        logger.info("Extracting requirements from SysML V2 model")
        logger.info("=" * 70)

        # Initialize client
        logger.info(f"Connecting to SysML V2 API: {args.api_url}")
        client = SysMLV2Client(api_url=args.api_url, api_token=args.api_token)

        # Initialize extractor
        extractor = RequirementExtractor(client)

        # Extract requirements
        logger.info(f"Extracting requirements from project: {args.project_id}")
        requirements = extractor.extract_requirements(
            project_id=args.project_id,
            commit_id=args.commit_id,
            include_usages=args.include_usages
        )

        # Save to file
        logger.info(f"Saving {len(requirements)} requirements to: {args.output}")
        extractor.save_requirements(requirements, args.output)

        logger.info("✓ Extraction complete")
        logger.info(f"  - Requirements extracted: {len(requirements)}")
        logger.info(f"  - Output file: {args.output}")

        return 0

    def _handle_generate(self, args) -> int:
        """Handle generate command"""
        logger.info("=" * 70)
        logger.info("Generating pytest tests from requirements")
        logger.info("=" * 70)

        # Load requirements
        logger.info(f"Loading requirements from: {args.input}")
        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1

        requirements = RequirementExtractor.load_requirements(args.input)
        logger.info(f"Loaded {len(requirements)} requirements")

        # Configure generator
        config = GeneratorConfig(
            output_dir=args.output_dir,
            system_module=args.system_module,
            use_hypothesis=not args.no_hypothesis,
            format_code=not args.no_format,
        )

        # Generate tests
        generator = PytestGenerator(config)

        if args.split_files:
            logger.info("Generating separate test file for each requirement...")
            generated_files = generator.generate_tests_per_requirement(requirements)
            logger.info("✓ Generation complete")
            logger.info(f"  - Test files generated: {len(generated_files)}")
            logger.info(f"  - Output directory: {args.output_dir}")
        else:
            logger.info("Generating single test file...")
            output_file = generator.generate_tests(requirements, args.output_file)
            logger.info("✓ Generation complete")
            logger.info(f"  - Tests generated: {len(requirements)}")
            logger.info(f"  - Output file: {output_file}")

        logger.info("\nNext steps:")
        logger.info(f"  1. Review generated tests in: {args.output_dir}")
        logger.info(f"  2. Implement system under test in: {args.system_module}")
        logger.info(f"  3. Run tests: pytest {args.output_dir}")
        logger.info(f"  4. Generate traceability: pytest {args.output_dir} --requirement-trace=trace.json")

        return 0

    def _handle_workflow(self, args) -> int:
        """Handle workflow command (extract + generate)"""
        logger.info("=" * 70)
        logger.info("Running full workflow: Extract + Generate")
        logger.info("=" * 70)

        # Step 1: Extract
        logger.info("\n[Step 1/2] Extracting requirements...")
        client = SysMLV2Client(api_url=args.api_url, api_token=args.api_token)
        extractor = RequirementExtractor(client)

        requirements = extractor.extract_requirements(
            project_id=args.project_id,
            commit_id=args.commit_id
        )

        # Save intermediate file
        extractor.save_requirements(requirements, args.requirements_file)
        logger.info(f"✓ Extracted {len(requirements)} requirements")

        # Step 2: Generate
        logger.info("\n[Step 2/2] Generating pytest tests...")
        config = GeneratorConfig(
            output_dir=args.output_dir,
            system_module=args.system_module,
            use_hypothesis=True,
            format_code=True,
        )

        generator = PytestGenerator(config)
        output_file = generator.generate_tests(requirements)

        logger.info("=" * 70)
        logger.info("✓ Workflow complete!")
        logger.info("=" * 70)
        logger.info(f"  - Requirements extracted: {len(requirements)}")
        logger.info(f"  - Requirements file: {args.requirements_file}")
        logger.info(f"  - Test file: {output_file}")
        logger.info("\nNext steps:")
        logger.info(f"  1. Review tests: {output_file}")
        logger.info(f"  2. Run tests: pytest {args.output_dir}")

        return 0

    def _add_sync_status_command(self, subparsers):
        """Add sync-status subcommand"""
        sync_status_parser = subparsers.add_parser(
            "sync-status",
            help="Check for requirement changes without applying them",
            description="Detect changes between old and new requirements"
        )

        sync_status_parser.add_argument(
            "--old",
            type=Path,
            required=True,
            help="Old requirements JSON file"
        )

        sync_status_parser.add_argument(
            "--new",
            type=Path,
            required=True,
            help="New requirements JSON file"
        )

        sync_status_parser.add_argument(
            "--format",
            choices=["text", "json", "markdown"],
            default="text",
            help="Output format (default: text)"
        )

        sync_status_parser.add_argument(
            "-o", "--output",
            type=Path,
            help="Output file (default: stdout)"
        )

        sync_status_parser.set_defaults(func=self._run_sync_status)

    def _add_sync_command(self, subparsers):
        """Add sync subcommand"""
        sync_parser = subparsers.add_parser(
            "sync",
            help="Apply requirement changes to test files",
            description="Synchronize test files with updated requirements"
        )

        sync_parser.add_argument(
            "--old",
            type=Path,
            required=True,
            help="Old requirements JSON file"
        )

        sync_parser.add_argument(
            "--new",
            type=Path,
            required=True,
            help="New requirements JSON file"
        )

        sync_parser.add_argument(
            "-o", "--output-dir",
            type=Path,
            required=True,
            help="Test output directory"
        )

        sync_parser.add_argument(
            "--strategy",
            choices=["full-regen", "surgical", "side-by-side", "hybrid"],
            default="hybrid",
            help="Sync strategy (default: hybrid)"
        )

        sync_parser.add_argument(
            "--auto-merge",
            choices=["minor", "moderate", "major"],
            help="Auto-merge changes up to this severity level"
        )

        sync_parser.add_argument(
            "--preview",
            action="store_true",
            help="Preview changes without applying"
        )

        sync_parser.add_argument(
            "--no-backup",
            action="store_true",
            help="Don't create backups before updating"
        )

        sync_parser.add_argument(
            "--report",
            type=Path,
            help="Generate HTML report"
        )

        sync_parser.set_defaults(func=self._run_sync)

    def _add_history_command(self, subparsers):
        """Add history subcommand"""
        history_parser = subparsers.add_parser(
            "history",
            help="Show requirement version history",
            description="Display version history for a requirement"
        )

        history_parser.add_argument(
            "--requirement-id",
            required=True,
            help="Requirement ID to show history for"
        )

        history_parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)"
        )

        history_parser.add_argument(
            "--state-dir",
            type=Path,
            help="Sync state directory (default: .sysml2pytest)"
        )

        history_parser.set_defaults(func=self._run_history)

    def _run_sync_status(self, args) -> int:
        """Run sync-status command"""
        logger.info("Checking for requirement changes...")

        # Load old requirements
        from .extractor import RequirementExtractor
        old_reqs = RequirementExtractor.load_requirements(args.old)
        new_reqs = RequirementExtractor.load_requirements(args.new)

        # Detect changes
        detector = SyncDetector()
        report = detector.detect_changes(old_reqs, new_reqs)

        # Output report
        if args.format == "text":
            if args.output:
                with open(args.output, 'w') as f:
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = f
                    report.print_summary()
                    sys.stdout = old_stdout
                logger.info(f"Report saved to {args.output}")
            else:
                report.print_summary()
        elif args.format == "json":
            import json
            report_dict = report.to_dict()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report_dict, f, indent=2)
                logger.info(f"Report saved to {args.output}")
            else:
                print(json.dumps(report_dict, indent=2))
        elif args.format == "markdown":
            md_report = report.to_markdown()
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(md_report)
                logger.info(f"Report saved to {args.output}")
            else:
                print(md_report)

        return 0

    def _run_sync(self, args) -> int:
        """Run sync command"""
        logger.info("=" * 70)
        logger.info("Synchronizing requirements and tests")
        logger.info("=" * 70)

        # Load requirements
        from .extractor import RequirementExtractor
        old_reqs = RequirementExtractor.load_requirements(args.old)
        new_reqs = RequirementExtractor.load_requirements(args.new)

        # Detect changes
        detector = SyncDetector()
        report = detector.detect_changes(old_reqs, new_reqs)

        logger.info(f"\nDetected {report.total_changes} changes:")
        logger.info(f"  Added: {len(report.added)}")
        logger.info(f"  Deleted: {len(report.deleted)}")
        logger.info(f"  Modified: {len(report.modified)}")

        if report.total_changes == 0:
            logger.info("\n✓ No changes detected - tests are up to date")
            return 0

        # Map strategy name to enum
        strategy_map = {
            "full-regen": UpdateStrategy.FULL_REGEN,
            "surgical": UpdateStrategy.SURGICAL,
            "side-by-side": UpdateStrategy.SIDE_BY_SIDE,
            "hybrid": UpdateStrategy.HYBRID,
        }
        strategy = strategy_map[args.strategy]

        if args.preview:
            logger.info("\n[PREVIEW MODE] - No changes will be applied\n")
            report.print_summary()
            return 0

        # Initialize updater and state manager
        updater = TestUpdater(create_backups=not args.no_backup)
        state_mgr = SyncStateManager()
        state_mgr.initialize()

        # Process modified requirements
        updates = []
        for change in report.modified:
            # Find test file for this requirement
            req_id = change.requirement_id
            req_state = state_mgr.state.get_requirement(req_id)

            if req_state and req_state.test_file:
                test_file = req_state.test_file
            else:
                # Try to find test file
                test_file = args.output_dir / f"test_{change.requirement_name.lower()}.py"

            if not test_file.exists():
                logger.warning(f"Test file not found for {req_id}: {test_file}")
                continue

            # Get new requirement
            new_req = next((r for r in new_reqs if (r.metadata.id or r.metadata.name) == req_id), None)
            if not new_req:
                continue

            # Get new version
            new_version = req_state.version + 1 if req_state else 2

            updates.append({
                'test_file': test_file,
                'requirement': new_req,
                'severity': change.severity,
                'new_version': new_version,
            })

        # Apply updates
        if updates:
            logger.info(f"\nUpdating {len(updates)} test files...")
            results = updater.update_multiple_tests(updates, strategy=strategy)

            # Print summary
            updater.print_update_summary(results)

            # Update state
            for result in results:
                if result.success:
                    # Find requirement
                    update_spec = next((u for u in updates if u['test_file'] == result.file_path), None)
                    if update_spec:
                        req = update_spec['requirement']
                        from .sync.fingerprint import compute_requirement_hash, create_fingerprint
                        content_hash = compute_requirement_hash(req)
                        fingerprint = create_fingerprint(req, version=result.version_new)

                        state_mgr.update_requirement(
                            requirement_id=req.metadata.id or req.metadata.name,
                            content_hash=content_hash,
                            version=result.version_new,
                            test_file=result.file_path,
                            has_custom_code=True,  # Assume true if surgical update
                            fingerprint=fingerprint,
                        )

            state_mgr.mark_synced()
            logger.info("\n✓ Sync complete!")
        else:
            logger.info("\nNo test files to update")

        return 0

    def _run_history(self, args) -> int:
        """Run history command"""
        logger.info(f"Requirement history for: {args.requirement_id}")
        logger.info("=" * 70)

        # Load state
        state_mgr = SyncStateManager(state_dir=args.state_dir)
        state_mgr.load()

        # Get requirement state
        req_state = state_mgr.state.get_requirement(args.requirement_id)

        if not req_state:
            logger.error(f"Requirement {args.requirement_id} not found in sync state")
            return 1

        # Display history
        if args.format == "text":
            print(f"Requirement ID: {req_state.requirement_id}")
            print(f"Current Version: {req_state.version}")
            print(f"Content Hash: {req_state.content_hash}")
            print(f"Last Updated: {req_state.last_updated.isoformat()}")
            print(f"Test File: {req_state.test_file}")
            print(f"Has Custom Code: {req_state.has_custom_code}")

            if req_state.fingerprint:
                print(f"\nFingerprint:")
                print(f"  Content Hash: {req_state.fingerprint.content_hash}")
                print(f"  Metadata Hash: {req_state.fingerprint.metadata_hash}")
                print(f"  Structure Hash: {req_state.fingerprint.structure_hash}")
                print(f"  Timestamp: {req_state.fingerprint.timestamp}")
        elif args.format == "json":
            import json
            print(json.dumps(req_state.to_dict(), indent=2))

        return 0


def main():
    """Main entry point for CLI"""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
