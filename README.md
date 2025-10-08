# sysml2pytest

Automatically convert SysML V2 requirements into executable pytest tests with property-based testing using Hypothesis.

## Features

- **Automatic Test Generation**: Convert SysML V2 requirements with attributes and constraints into pytest tests
- **Property-Based Testing**: Generate Hypothesis test strategies from SysML constraints
- **Intelligent Synchronization**: Update tests when requirements change while preserving custom code
- **Change Detection**: Automatically classify changes as MINOR, MODERATE, or MAJOR
- **Requirement Traceability**: Track requirement-to-test relationships with JSON and Markdown reports
- **Protected Code Regions**: Separate generated and custom code sections

## Installation

### Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/redasasin4/Sysml_To_Pytest.git
cd Sysml_To_Pytest
uv sync

# Verify installation
uv run sysml2pytest --version
```

### Using pip

```bash
git clone https://github.com/redasasin4/Sysml_To_Pytest.git
cd Sysml_To_Pytest
pip install -e .
```

## Requirements

- Python 3.8+ (3.12 recommended)
- SysML V2 API Services (for requirement extraction)

## Quick Start

```bash
# Run the example demo
cd examples
uv run python demo_workflow.py

# Run generated tests
uv run pytest tests/test_generated_requirements.py -v

# Generate traceability reports
uv run pytest tests/test_generated_requirements.py --requirement-trace=trace.json
```

**Note:** Full SysML V2 API integration requires a running server. See [docs/SYSML_V2_API_SETUP.md](docs/SYSML_V2_API_SETUP.md) for setup instructions. The examples work with mock data.

## How It Works

### 1. Extract Requirements

Extract requirements from SysML V2 API:

```bash
uv run sysml2pytest extract \
    --api-url http://localhost:9000 \
    --project-id my-project \
    --output requirements.json
```

### 2. Generate Tests

Convert requirements to pytest tests:

```bash
uv run sysml2pytest generate \
    --input requirements.json \
    --output-dir tests/ \
    --system-module my_system
```

**Example Input (SysML V2):**
```sysml
requirement TreeHeightRequirement {
    attribute treeHeight: Integer;
    assume constraint { treeHeight > 0 }
    require constraint { 150 <= treeHeight and treeHeight <= 200 }
}
```

**Generated Output (pytest):**
```python
@pytest.mark.requirement(id="REQ-001", name="TreeHeightRequirement", version=1)
@given(treeHeight=st.integers(min_value=150, max_value=200))
def test_tree_height_requirement(treeHeight):
    """The Christmas tree shall be at least 150 cm and maximum 200 cm high."""

    # SYSML2PYTEST-CUSTOM-START
    # Add your custom test code here - preserved during sync
    # SYSML2PYTEST-CUSTOM-END

    assert validate_tree_height(treeHeight)
```

### 3. Sync When Requirements Change

Update tests when requirements change:

```bash
# Check what changed
uv run sysml2pytest sync-status \
    --old requirements.json \
    --new requirements_updated.json

# Apply changes (preserves custom code)
uv run sysml2pytest sync \
    --old requirements.json \
    --new requirements_updated.json \
    --output-dir tests/ \
    --strategy hybrid
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `extract` | Extract requirements from SysML V2 API |
| `generate` | Generate pytest tests from requirements JSON |
| `sync-status` | Check for requirement changes (dry run) |
| `sync` | Apply requirement changes to existing tests |
| `history` | Show version history for a requirement |

Run `uv run sysml2pytest --help` for detailed usage.

## Sync Strategies

| Strategy | Description | Use When |
|----------|-------------|----------|
| `full-regen` | Delete and regenerate all tests | No custom code exists |
| `surgical` | Update generated sections, preserve custom code | Changes are minor/moderate |
| `side-by-side` | Generate `.new` files for manual merge | Major changes requiring review |
| `hybrid` | Auto-choose based on change severity | Unsure (recommended default) |

## Change Classification

- **MINOR**: Documentation only → Auto-merge
- **MODERATE**: Constraint bounds changed → Surgical update
- **MAJOR**: Attributes added/removed → Manual review

## Protected Code Regions

Generated tests include protected regions:

```python
# SYSML2PYTEST-GENERATED-START
# Auto-generated code - updated during sync
# SYSML2PYTEST-GENERATED-END

# SYSML2PYTEST-CUSTOM-START
# Your custom code - PRESERVED during sync
# SYSML2PYTEST-CUSTOM-END
```

## Constraint Transpilation

SysML constraints are automatically converted to Hypothesis strategies:

| SysML Type | Hypothesis Strategy |
|------------|---------------------|
| `Integer [min, max]` | `st.integers(min_value=min, max_value=max)` |
| `Real [min, max]` | `st.floats(min_value=min, max_value=max)` |
| `Boolean` | `st.booleans()` |
| `String` | `st.text()` |
| `Enumeration` | `st.sampled_from([...])` |

## Workflow Example

### Initial Setup

```bash
# 1. Extract requirements
uv run sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements.json

# 2. Generate tests
uv run sysml2pytest generate -i requirements.json -o tests/

# 3. Add custom test code in CUSTOM regions
# Edit tests/test_*.py

# 4. Run tests
uv run pytest tests/
```

### When Requirements Change

```bash
# 1. Extract updated requirements
uv run sysml2pytest extract --api-url http://localhost:9000 --project-id my-project -o requirements_new.json

# 2. Check changes
uv run sysml2pytest sync-status --old requirements.json --new requirements_new.json

# 3. Preview sync
uv run sysml2pytest sync --old requirements.json --new requirements_new.json -o tests/ --preview

# 4. Apply sync
uv run sysml2pytest sync --old requirements.json --new requirements_new.json -o tests/ --strategy hybrid

# 5. Verify tests
uv run pytest tests/

# 6. Commit changes
mv requirements_new.json requirements.json
git add requirements.json tests/
git commit -m "Sync: Updated requirements"
```

## SysML V2 API Setup

### Using Docker

```bash
docker run -p 9000:9000 sysml/sysml-v2-api-services
```

### From Source

See [docs/SYSML_V2_API_SETUP.md](docs/SYSML_V2_API_SETUP.md) for detailed instructions.

## Project Structure

```
sysml2pytest/
├── sysml2pytest/
│   ├── extractor/         # SysML V2 API client and extraction
│   ├── transpiler/        # Constraint to Python/Hypothesis conversion
│   ├── generator/         # Pytest test file generation
│   ├── sync/              # Intelligent sync system
│   ├── plugin/            # Pytest plugin for traceability
│   └── cli.py             # Command-line interface
├── tests/                 # Unit and integration tests
├── examples/              # Example projects and demos
└── docs/                  # Documentation
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=sysml2pytest --cov-report=html

# Specific test file
uv run pytest tests/test_sync_state.py -v
```

### Code Formatting

```bash
# Format code
uv run black sysml2pytest/ tests/

# Lint code
uv run ruff check sysml2pytest/ tests/
```

## Examples

See the `examples/` directory for a complete Christmas Tree requirement demonstration.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Technical architecture details
- [SysML V2 API Setup](docs/SYSML_V2_API_SETUP.md) - API server setup guide
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- SysML V2 support based on OMG SysML v2 specification
- Property-based testing powered by [Hypothesis](https://hypothesis.readthedocs.io/)
- Fast dependency management with [uv](https://github.com/astral-sh/uv)

## Status

**Current Version:** 0.1.0

- ✅ Requirement extraction from SysML V2 API
- ✅ Pytest test generation with Hypothesis
- ✅ Constraint transpilation
- ✅ Intelligent sync system with custom code preservation
- ✅ CLI with extract, generate, sync commands
- ✅ Version tracking and change detection
- ⏳ Full integration tests pending

**Test Coverage:** 22% overall, 100% for sync state manager

## Support

For issues, questions, or feature requests, please [open an issue](https://github.com/redasasin4/Sysml_To_Pytest/issues) on GitHub.
