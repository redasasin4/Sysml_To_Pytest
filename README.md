# sysml2pytest

Convert SysML V2 requirements into executable pytest tests with property-based testing.

## What It Does

sysml2pytest automatically generates pytest test files from SysML V2 requirements, complete with:
- Property-based tests using Hypothesis
- Constraint-based test strategies
- Requirement traceability
- **Intelligent sync to preserve custom test code when requirements change**

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/yourusername/sysml2pytest.git
cd sysml2pytest
uv sync

# Run the example demo
cd examples
uv run python demo_workflow.py

# Run generated tests
uv run pytest tests/test_generated_requirements.py -v

# Generate traceability reports
uv run pytest tests/test_generated_requirements.py --requirement-trace=trace.json
uv run pytest tests/test_generated_requirements.py --requirement-trace-md=trace.md
```

**Note:** The full SysML V2 API integration requires a running SysML V2 API server. See [docs/SYSML_V2_API_SETUP.md](docs/SYSML_V2_API_SETUP.md) for setup instructions. The examples directory includes a demo that works with mock data.

## Key Features

### 1. Automatic Test Generation

Converts SysML V2 requirements with attributes and constraints into pytest tests:

**SysML V2 Input:**
```
requirement TreeHeightRequirement {
    attribute treeHeight: Integer;
    assume constraint { treeHeight > 0 }
    require constraint { 150 <= treeHeight and treeHeight <= 200 }
}
```

**Generated pytest Output:**
```python
@pytest.mark.requirement(id="REQ-001", name="TreeHeightRequirement", version=1)
@given(treeHeight=st.integers(min_value=150, max_value=200))
def test_tree_height_requirement(treeHeight):
    """The Christmas tree shall be at least 150 cm and maximum 200 cm high."""

    # SYSML2PYTEST-CUSTOM-START
    # Add your custom test code here - preserved during sync!
    # SYSML2PYTEST-CUSTOM-END

    assert validate_tree_height(treeHeight)
```

### 2. Property-Based Testing

Uses Hypothesis to generate test strategies automatically from requirement constraints:
- Integer ranges → `st.integers(min_value=X, max_value=Y)`
- Real ranges → `st.floats(min_value=X, max_value=Y)`
- Boolean → `st.booleans()`
- Enumerations → `st.sampled_from([...])`

### 3. Intelligent Synchronization

**The killer feature**: When requirements change, sysml2pytest can update your tests while preserving custom code:

```bash
# Check what changed
sysml2pytest sync-status --old requirements.json --new requirements_updated.json

# Apply changes (preserves custom code in CUSTOM regions)
sysml2pytest sync --old requirements.json --new requirements_updated.json -o tests/ --strategy hybrid
```

**Sync Strategies:**
- `full-regen` - Delete and regenerate (loses custom code)
- `surgical` - Update generated sections, preserve custom code
- `side-by-side` - Generate `.new` files for manual merge
- `hybrid` - Auto-choose based on change severity (recommended)

### 4. Change Detection

Automatically detects and classifies requirement changes:
- **MINOR**: Documentation updates → Auto-merge
- **MODERATE**: Constraint bounds changed → Surgical update
- **MAJOR**: Attributes added/removed → Side-by-side review

### 5. Protected Code Regions

Tests have clearly marked regions:
```python
# SYSML2PYTEST-GENERATED-START
# Auto-generated code - updated during sync
# SYSML2PYTEST-GENERATED-END

# SYSML2PYTEST-CUSTOM-START
# Your custom code - PRESERVED during sync
# SYSML2PYTEST-CUSTOM-END
```

### 6. Version Tracking

Each test tracks:
- Requirement ID
- Content hash (for change detection)
- Version number
- Generation timestamp

## CLI Commands

### extract
Extract requirements from SysML V2 API:
```bash
uv run sysml2pytest extract \
    --api-url http://localhost:9000 \
    --project-id christmas-tree \
    --output requirements.json
```

### generate
Generate pytest tests from requirements:
```bash
uv run sysml2pytest generate \
    --input requirements.json \
    --output-dir tests/ \
    --system-module my_system
```

### sync-status
Check for requirement changes (dry run):
```bash
uv run sysml2pytest sync-status \
    --old requirements.json \
    --new requirements_updated.json \
    --format text
```

**Output:**
```
Total Changes: 3
  Added:    1
  Deleted:  1
  Modified: 1 (MODERATE - bounds changed)
```

### sync
Apply requirement changes to tests:
```bash
uv run sysml2pytest sync \
    --old requirements.json \
    --new requirements_updated.json \
    --output-dir tests/ \
    --strategy hybrid \
    --preview  # Optional: see changes before applying
```

### history
Show version history for a requirement:
```bash
uv run sysml2pytest history --requirement-id REQ-001
```

## Workflow Example

### Initial Setup
```bash
# 1. Extract requirements from your SysML V2 model
uv run sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements.json

# 2. Generate tests
uv run sysml2pytest generate -i requirements.json -o tests/

# 3. Add custom test code in CUSTOM regions
# Edit tests/test_*.py and add your custom validation

# 4. Run tests
uv run pytest tests/
```

### When Requirements Change
```bash
# 1. Extract updated requirements
uv run sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements_new.json

# 2. Check what changed
uv run sysml2pytest sync-status --old requirements.json --new requirements_new.json

# 3. Preview changes
uv run sysml2pytest sync --old requirements.json --new requirements_new.json -o tests/ --preview

# 4. Apply sync (preserves your custom code!)
uv run sysml2pytest sync --old requirements.json --new requirements_new.json -o tests/ --strategy hybrid

# 5. Verify tests still pass
uv run pytest tests/

# 6. Commit
mv requirements_new.json requirements.json
git add requirements.json tests/
git commit -m "Sync: Updated requirements"
```

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver (10-100x faster than pip).

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/sysml2pytest.git
cd sysml2pytest

# Install dependencies and create virtual environment
uv sync

# Install with dev dependencies (for running tests)
uv sync --extra dev

# Run commands with uv
uv run sysml2pytest --version
uv run pytest
```

**Why uv?**
- ⚡ 10-100x faster than pip
- 🔒 Automatic dependency locking (uv.lock)
- 📦 Built-in virtual environment management
- 🎯 Reproducible builds across machines

### Using pip

```bash
git clone https://github.com/yourusername/sysml2pytest.git
cd sysml2pytest
pip install -e .
pip install -e ".[dev]"  # For development
```

### Requirements
- Python 3.8+ (Python 3.12 recommended)
- pytest
- hypothesis
- jinja2
- requests
- SysML V2 API Services (for extraction)

## SysML V2 API Setup

To extract requirements, you need a running SysML V2 API server:

### Quick Start with Docker
```bash
docker run -p 9000:9000 sysml/sysml-v2-api-services
```

### From Source
See `docs/SYSML_V2_API_SETUP.md` for detailed setup instructions.

## Project Structure

```
sysml2pytest/
├── extractor/          # SysML V2 API client and requirement extraction
├── transpiler/         # Convert SysML constraints to Python/Hypothesis
├── generator/          # Generate pytest test files
├── sync/               # Intelligent sync system
│   ├── fingerprint.py  # Content-based change detection
│   ├── detector.py     # Detect and classify changes
│   ├── state.py        # Persistent sync state
│   ├── parser.py       # Parse existing test files
│   └── updater.py      # Apply changes to tests
├── plugin/             # Pytest plugin for traceability
└── cli.py              # Command-line interface
```

## Development

### Running Tests

```bash
# With uv (recommended)
uv run pytest

# Run with coverage
uv run pytest --cov=sysml2pytest --cov-report=html

# Run specific test suite
uv run pytest tests/test_sync_state.py -v

# With pip
pytest
```

### Code Formatting

```bash
# Format with black
uv run black sysml2pytest/ tests/

# Lint with ruff
uv run ruff check sysml2pytest/ tests/
```

## Example

See `examples/` for a complete Christmas Tree requirement example.

## Architecture

For technical details, see `ARCHITECTURE.md`.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with Claude Code
- SysML V2 support based on OMG SysML v2 specification
- Property-based testing powered by [Hypothesis](https://hypothesis.readthedocs.io/)
- Fast dependency management with [uv](https://github.com/astral-sh/uv)

## Status

- ✅ Requirement extraction from SysML V2 API
- ✅ Pytest test generation with Hypothesis
- ✅ Constraint transpilation
- ✅ Intelligent sync system with custom code preservation
- ✅ CLI with extract, generate, sync commands
- ✅ Version tracking and change detection
- ⏳ Full integration tests pending

**Current Test Coverage**: 22% overall, 100% for sync state manager

## Changelog

### v0.1.0 (2025-10-07)
- Initial release
- Full sync system implementation
- CLI commands: extract, generate, sync-status, sync, history
- Protected code regions (GENERATED vs CUSTOM)
- Four sync strategies (full-regen, surgical, side-by-side, hybrid)
- Change detection and classification (MINOR, MODERATE, MAJOR)
- Version tracking with content-based fingerprinting
- Persistent state management
- Modern packaging with uv support
- Reproducible builds with uv.lock

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
