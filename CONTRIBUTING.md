# Contributing to sysml2pytest

Thank you for your interest in contributing to sysml2pytest! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher (Python 3.12 recommended)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sysml2pytest.git
   cd sysml2pytest
   ```

2. **Install dependencies with uv (recommended)**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies including dev tools
   uv sync --extra dev
   ```

   Or with pip:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Verify installation**
   ```bash
   uv run pytest
   uv run sysml2pytest --version
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=sysml2pytest --cov-report=html

# Run specific test file
uv run pytest tests/test_generator.py -v

# Run tests matching a pattern
uv run pytest -k "test_sync"
```

### Code Formatting and Linting

This project uses [Black](https://black.readthedocs.io/) for code formatting and [Ruff](https://docs.astral.sh/ruff/) for linting.

```bash
# Format code with Black
uv run black sysml2pytest/ tests/ examples/

# Lint with Ruff
uv run ruff check sysml2pytest/ tests/

# Auto-fix linting issues
uv run ruff check --fix sysml2pytest/ tests/
```

### Code Style Guidelines

- Follow PEP 8 style guidelines (enforced by Black and Ruff)
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write docstrings for public functions and classes (Google style preferred)
- Keep functions focused and single-purpose

Example docstring format:
```python
def extract_requirements(project_id: str, commit_id: Optional[str] = None) -> List[Requirement]:
    """
    Extract all requirements from a SysML V2 project.

    Args:
        project_id: SysML V2 project identifier
        commit_id: Specific commit (optional, uses HEAD if not provided)

    Returns:
        List of extracted Requirement objects

    Raises:
        ConnectionError: If unable to connect to SysML V2 API
        ValueError: If project_id is invalid
    """
```

## Making Contributions

### Types of Contributions

We welcome the following types of contributions:

1. **Bug fixes** - Fix issues and improve reliability
2. **Features** - Add new functionality
3. **Documentation** - Improve docs, examples, and guides
4. **Tests** - Expand test coverage
5. **Performance improvements** - Optimize code

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**
   ```bash
   uv run pytest
   uv run black sysml2pytest/ tests/
   uv run ruff check sysml2pytest/ tests/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add new feature description"
   ```

   Commit message format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions or changes
   - `refactor:` - Code refactoring
   - `perf:` - Performance improvements
   - `chore:` - Build process or auxiliary tool changes

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the GitHub repository
   - Click "New Pull Request"
   - Provide a clear description of the changes
   - Reference any related issues

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass (`uv run pytest`)
- [ ] New code has appropriate test coverage
- [ ] Documentation is updated if needed
- [ ] Commit messages follow the convention
- [ ] No unnecessary files are included (check `.gitignore`)

## Project Structure

```
sysml2pytest/
├── sysml2pytest/          # Main package
│   ├── extractor/         # SysML V2 API client and extraction
│   ├── transpiler/        # Constraint to Python/Hypothesis conversion
│   ├── generator/         # Pytest test file generation
│   ├── sync/              # Intelligent sync system
│   ├── plugin/            # Pytest plugin for traceability
│   └── cli.py             # Command-line interface
├── tests/                 # Unit and integration tests
├── examples/              # Example projects and demos
├── docs/                  # Documentation
└── pyproject.toml         # Project configuration
```

## Adding New Features

### Adding a New CLI Command

1. Add the command handler in `sysml2pytest/cli.py`
2. Add corresponding tests in `tests/test_cli.py`
3. Update README.md with usage examples
4. Update `docs/` with detailed documentation

### Adding a New Sync Strategy

1. Implement the strategy in `sysml2pytest/sync/updater.py`
2. Add tests in `tests/test_sync_updater.py`
3. Document the strategy in README.md

### Adding Support for New Constraint Types

1. Update the transpiler in `sysml2pytest/transpiler/transpiler.py`
2. Add Hypothesis strategy generation in `sysml2pytest/transpiler/hypothesis_strategy.py`
3. Add comprehensive tests
4. Update documentation with examples

## Testing Guidelines

### Writing Tests

- Use pytest fixtures for common setup
- Test both happy paths and edge cases
- Use property-based testing with Hypothesis where appropriate
- Mock external dependencies (API calls, file I/O when needed)
- Aim for >80% code coverage

Example test structure:
```python
def test_requirement_extraction():
    """Test that requirements are correctly extracted from SysML V2 model."""
    # Arrange
    mock_client = MockSysMLClient()
    extractor = RequirementExtractor(mock_client)

    # Act
    requirements = extractor.extract_requirements("test-project")

    # Assert
    assert len(requirements) == 3
    assert requirements[0].metadata.id == "REQ-001"
```

### Test Organization

- Unit tests: Test individual functions/classes in isolation
- Integration tests: Test component interactions
- End-to-end tests: Test complete workflows

## Documentation

### Documentation Standards

- Keep README.md up to date
- Add docstrings to all public APIs
- Include examples in documentation
- Update CHANGELOG.md for significant changes

### Building Documentation Locally

```bash
# If we add Sphinx or mkdocs in the future
# Example: mkdocs serve
```

## Release Process

Maintainers handle releases. The process:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions builds and publishes to PyPI (if configured)

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/yourusername/sysml2pytest/discussions)
- **Bug reports?** Open a [GitHub Issue](https://github.com/yourusername/sysml2pytest/issues)
- **Feature requests?** Open a [GitHub Issue](https://github.com/yourusername/sysml2pytest/issues) with the "enhancement" label

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## License

By contributing to sysml2pytest, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to sysml2pytest! 🎉
