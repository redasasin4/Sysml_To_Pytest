"""
Unit tests for CLI
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from sysml2pytest.cli import CLI
from sysml2pytest.extractor.models import Requirement, RequirementMetadata


class TestCLI:
    """Test CLI application"""

    def setup_method(self):
        """Set up test fixtures"""
        self.cli = CLI()

    def test_cli_initialization(self):
        """Test CLI initializes correctly"""
        assert self.cli.parser is not None

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help"""
        exit_code = self.cli.run([])

        assert exit_code == 1

    def test_version_command(self, capsys):
        """Test --version flag"""
        with pytest.raises(SystemExit) as exc_info:
            self.cli.run(["--version"])

        assert exc_info.value.code == 0

    def test_extract_command_missing_args(self):
        """Test extract command with missing required arguments"""
        with pytest.raises(SystemExit):
            self.cli.run(["extract"])

    def test_generate_command_missing_args(self):
        """Test generate command with missing required arguments"""
        with pytest.raises(SystemExit):
            self.cli.run(["generate"])

    @patch("sysml2pytest.cli.SysMLV2Client")
    @patch("sysml2pytest.cli.RequirementExtractor")
    def test_extract_command_success(self, mock_extractor_class, mock_client_class, tmp_path):
        """Test successful extract command"""
        output_file = tmp_path / "requirements.json"

        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract_requirements.return_value = []
        mock_extractor_class.return_value = mock_extractor

        exit_code = self.cli.run([
            "extract",
            "--api-url", "http://localhost:9000",
            "--project-id", "test-project",
            "--output", str(output_file),
        ])

        assert exit_code == 0
        mock_extractor.extract_requirements.assert_called_once()
        mock_extractor.save_requirements.assert_called_once()

    @patch("sysml2pytest.cli.RequirementExtractor")
    @patch("sysml2pytest.cli.PytestGenerator")
    def test_generate_command_success(self, mock_generator_class, mock_extractor_class, tmp_path):
        """Test successful generate command"""
        input_file = tmp_path / "requirements.json"
        output_dir = tmp_path / "tests"
        output_dir.mkdir()

        # Create mock requirements file
        mock_req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="TestReq",
                qualified_name="Test::TestReq",
            )
        )
        input_file.write_text(json.dumps({
            "requirements": [mock_req.to_dict()],
            "count": 1,
        }))

        # Mock the generator
        mock_generator = MagicMock()
        mock_generator.generate_tests.return_value = output_dir / "test_output.py"
        mock_generator_class.return_value = mock_generator

        exit_code = self.cli.run([
            "generate",
            "--input", str(input_file),
            "--output-dir", str(output_dir),
        ])

        assert exit_code == 0
        mock_generator.generate_tests.assert_called_once()

    def test_generate_command_file_not_found(self, tmp_path):
        """Test generate command with non-existent input file"""
        input_file = tmp_path / "nonexistent.json"

        exit_code = self.cli.run([
            "generate",
            "--input", str(input_file),
            "--output-dir", str(tmp_path),
        ])

        assert exit_code == 1

    @patch("sysml2pytest.cli.RequirementExtractor")
    @patch("sysml2pytest.cli.PytestGenerator")
    def test_generate_command_split_files(self, mock_generator_class, mock_extractor_class, tmp_path):
        """Test generate command with --split-files"""
        input_file = tmp_path / "requirements.json"

        # Create mock requirements file
        mock_req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="TestReq",
                qualified_name="Test::TestReq",
            )
        )
        input_file.write_text(json.dumps({
            "requirements": [mock_req.to_dict()],
            "count": 1,
        }))

        # Mock the generator
        mock_generator = MagicMock()
        mock_generator.generate_tests_per_requirement.return_value = {
            "REQ-001": tmp_path / "test_testreq.py"
        }
        mock_generator_class.return_value = mock_generator

        exit_code = self.cli.run([
            "generate",
            "--input", str(input_file),
            "--output-dir", str(tmp_path),
            "--split-files",
        ])

        assert exit_code == 0
        mock_generator.generate_tests_per_requirement.assert_called_once()

    @patch("sysml2pytest.cli.SysMLV2Client")
    @patch("sysml2pytest.cli.RequirementExtractor")
    @patch("sysml2pytest.cli.PytestGenerator")
    def test_workflow_command(self, mock_generator_class, mock_extractor_class, mock_client_class, tmp_path):
        """Test workflow command (extract + generate)"""
        # Mock extractor
        mock_extractor = MagicMock()
        mock_extractor.extract_requirements.return_value = []
        mock_extractor_class.return_value = mock_extractor

        # Mock generator
        mock_generator = MagicMock()
        mock_generator.generate_tests.return_value = tmp_path / "test_output.py"
        mock_generator_class.return_value = mock_generator

        exit_code = self.cli.run([
            "workflow",
            "--api-url", "http://localhost:9000",
            "--project-id", "test-project",
            "--output-dir", str(tmp_path),
        ])

        assert exit_code == 0
        mock_extractor.extract_requirements.assert_called_once()
        mock_generator.generate_tests.assert_called_once()

    def test_verbose_flag(self, tmp_path):
        """Test verbose flag enables debug logging"""
        # This test just ensures the flag is parsed correctly
        # Actual logging behavior would need more complex testing
        with patch("sysml2pytest.cli.logging.getLogger") as mock_logger:
            with pytest.raises(SystemExit):
                # Will fail because extract needs args, but verbose will be processed
                self.cli.run(["--verbose", "extract"])


class TestCLIHelp:
    """Test CLI help messages"""

    def test_main_help(self):
        """Test main help message"""
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.run(["--help"])

    def test_extract_help(self):
        """Test extract command help"""
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.run(["extract", "--help"])

    def test_generate_help(self):
        """Test generate command help"""
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.run(["generate", "--help"])

    def test_workflow_help(self):
        """Test workflow command help"""
        cli = CLI()
        with pytest.raises(SystemExit):
            cli.run(["workflow", "--help"])


class TestCLIArguments:
    """Test CLI argument parsing"""

    def setup_method(self):
        """Set up test fixtures"""
        self.cli = CLI()

    def test_extract_with_all_options(self):
        """Test extract with all optional arguments"""
        with patch("sysml2pytest.cli.SysMLV2Client"):
            with patch("sysml2pytest.cli.RequirementExtractor") as mock_extractor_class:
                mock_extractor = MagicMock()
                mock_extractor.extract_requirements.return_value = []
                mock_extractor_class.return_value = mock_extractor

                exit_code = self.cli.run([
                    "extract",
                    "--api-url", "http://localhost:9000",
                    "--project-id", "test-project",
                    "--commit-id", "abc123",
                    "--api-token", "secret-token",
                    "--output", "custom_output.json",
                    "--include-usages",
                ])

                assert exit_code == 0

    def test_generate_with_all_options(self, tmp_path):
        """Test generate with all optional arguments"""
        input_file = tmp_path / "requirements.json"

        # Create mock requirements file
        input_file.write_text(json.dumps({
            "requirements": [],
            "count": 0,
        }))

        with patch("sysml2pytest.cli.PytestGenerator") as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator.generate_tests.return_value = tmp_path / "test_output.py"
            mock_generator_class.return_value = mock_generator

            exit_code = self.cli.run([
                "generate",
                "--input", str(input_file),
                "--output-dir", str(tmp_path),
                "--output-file", str(tmp_path / "custom_test.py"),
                "--system-module", "my_custom_module",
                "--no-hypothesis",
                "--no-format",
            ])

            assert exit_code == 0
