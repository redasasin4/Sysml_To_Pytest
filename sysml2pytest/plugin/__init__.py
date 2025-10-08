"""
Pytest plugin for SysML V2 requirements traceability

Provides:
- Custom @pytest.mark.requirement marker
- Requirements coverage tracking
- Traceability reporting
"""

from .plugin import pytest_configure, pytest_addoption
from .markers import RequirementMarker
from .traceability import TraceabilityCollector, TraceabilityReport

__all__ = [
    "pytest_configure",
    "pytest_addoption",
    "RequirementMarker",
    "TraceabilityCollector",
    "TraceabilityReport",
]
