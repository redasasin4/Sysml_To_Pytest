# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-07

### Added
- Initial release of sysml2pytest
- SysML V2 requirement extraction from API
- Automatic pytest test generation with Hypothesis
- Property-based testing strategies from SysML constraints
- Intelligent sync system with 4 strategies (full-regen, surgical, side-by-side, hybrid)
- Protected code regions (GENERATED vs CUSTOM)
- Change detection and classification (MINOR, MODERATE, MAJOR)
- Version tracking with content-based fingerprinting
- Persistent state management for sync
- Pytest plugin for requirement traceability
- CLI commands: extract, generate, sync-status, sync, history
- Comprehensive test suite with >20% coverage
- Full documentation and examples
- Christmas Tree and Battery system examples
- Modern packaging with uv support
- Reproducible builds with uv.lock

### Features
- **Requirement Extraction**: Extract requirements from SysML V2 models via API
- **Test Generation**: Automatically generate pytest tests with Hypothesis strategies
- **Constraint Transpilation**: Convert SysML constraints to Python/Hypothesis code
- **Intelligent Sync**: Update tests when requirements change while preserving custom code
- **Traceability**: Full requirement-to-test traceability with JSON and Markdown reports
- **Property-Based Testing**: Leverage Hypothesis for comprehensive test coverage
- **Version Control**: Track requirement versions and detect changes

### Documentation
- Comprehensive README with quick start and examples
- CONTRIBUTING.md with development guidelines
- SysML V2 API setup guide
- Architecture documentation
- Example workflows and demos

### Infrastructure
- Modern Python packaging with pyproject.toml
- uv for fast dependency management
- Black for code formatting
- Ruff for linting
- pytest with coverage reporting
- GitHub-ready project structure

[Unreleased]: https://github.com/yourusername/sysml2pytest/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/sysml2pytest/releases/tag/v0.1.0
