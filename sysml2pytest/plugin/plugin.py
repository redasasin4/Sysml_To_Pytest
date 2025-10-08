"""
Pytest plugin implementation for requirements traceability
"""

import pytest
import logging
from pathlib import Path
from typing import Optional

from .markers import RequirementMarker
from .traceability import TraceabilityCollector

logger = logging.getLogger(__name__)

# Global collector instance
_collector: Optional[TraceabilityCollector] = None


def pytest_addoption(parser):
    """Add command-line options for requirements plugin"""
    group = parser.getgroup("requirements", "Requirements traceability")

    group.addoption(
        "--requirement-trace",
        action="store",
        dest="requirement_trace",
        default=None,
        help="Output file for requirements traceability report (JSON)",
    )

    group.addoption(
        "--requirement-trace-md",
        action="store",
        dest="requirement_trace_md",
        default=None,
        help="Output file for requirements traceability report (Markdown)",
    )

    group.addoption(
        "--requirement-summary",
        action="store_true",
        dest="requirement_summary",
        default=False,
        help="Print requirements traceability summary to console",
    )


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "requirement(id, name, ...): mark test to trace to a SysML V2 requirement"
    )

    # Initialize collector
    global _collector
    _collector = TraceabilityCollector()


def pytest_collection_modifyitems(session, config, items):
    """Process collected items to extract requirement markers"""
    global _collector

    for item in items:
        # Look for requirement marker
        requirement_marker = item.get_closest_marker("requirement")

        if requirement_marker:
            # Extract requirement info
            req_marker = RequirementMarker.from_marker(requirement_marker)
            _collector.register_requirement(req_marker.id, req_marker.name)
        else:
            # Track tests without requirement markers
            _collector.record_test_without_requirement(item.nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook into test execution to record results"""
    global _collector

    outcome = yield
    report = outcome.get_result()

    # Only process test call phase (not setup/teardown)
    if report.when == "call":
        requirement_marker = item.get_closest_marker("requirement")

        if requirement_marker:
            req_marker = RequirementMarker.from_marker(requirement_marker)

            # Get error message if failed
            error_msg = None
            if report.failed:
                error_msg = str(report.longrepr) if report.longrepr else "Unknown error"

            _collector.record_test(
                requirement_marker=req_marker,
                test_name=item.nodeid,
                test_file=str(item.fspath),
                outcome=report.outcome,
                duration=report.duration,
                error_message=error_msg
            )


def pytest_sessionfinish(session, exitstatus):
    """Generate reports after test session completes"""
    global _collector

    config = session.config
    report = _collector.generate_report()

    # Save JSON report if requested
    if config.option.requirement_trace:
        output_file = Path(config.option.requirement_trace)
        report.save_json(output_file)

    # Save Markdown report if requested
    if config.option.requirement_trace_md:
        output_file = Path(config.option.requirement_trace_md)
        report.save_markdown(output_file)

    # Print summary if requested
    if config.option.requirement_summary:
        report.print_summary()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add requirements summary to terminal output"""
    global _collector

    if config.option.requirement_summary:
        report = _collector.generate_report()

        terminalreporter.section("Requirements Traceability")
        terminalreporter.write_line(
            f"Coverage: {report.coverage_percentage:.1f}% "
            f"({report.tested_requirements}/{report.total_requirements} requirements)"
        )
        terminalreporter.write_line(
            f"Verification: {report.verification_percentage:.1f}% "
            f"({report.verified_requirements}/{report.total_requirements} verified)"
        )

        if report.untested_requirements:
            terminalreporter.write_line(
                f"Untested: {len(report.untested_requirements)} requirements",
                yellow=True
            )
