"""
Tests for sync change detector module
"""

import pytest

from sysml2pytest.sync.detector import (
    SyncDetector,
    RequirementChange,
    ChangeType,
    ChangeSeverity,
)
from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
)


@pytest.fixture
def detector():
    """Create SyncDetector instance"""
    return SyncDetector()


@pytest.fixture
def req_list_v1():
    """Create list of requirements (version 1)"""
    return [
        Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Req1",
                qualified_name="Requirements::Req1",
                documentation="First requirement"
            ),
            attributes=[
                RequirementAttribute(
                    name="height",
                    type="Integer",
                    min_value=150,
                    max_value=200
                )
            ],
            constraints=[
                Constraint(
                    type="require",
                    expression="150 <= height and height <= 200"
                )
            ]
        ),
        Requirement(
            metadata=RequirementMetadata(
                id="REQ-002",
                name="Req2",
                qualified_name="Requirements::Req2",
                documentation="Second requirement"
            ),
            attributes=[
                RequirementAttribute(
                    name="count",
                    type="Integer",
                    min_value=10,
                    max_value=50
                )
            ]
        )
    ]


class TestSyncDetector:
    """Tests for SyncDetector class"""

    def test_no_changes(self, detector, req_list_v1):
        """Test detecting no changes when requirements are identical"""
        report = detector.detect_changes(req_list_v1, req_list_v1)

        assert report.total_changes == 0
        assert len(report.added) == 0
        assert len(report.deleted) == 0
        assert len(report.modified) == 0
        assert len(report.unchanged) == 2

    def test_detect_added_requirement(self, detector, req_list_v1):
        """Test detecting added requirements"""
        new_req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-003",
                name="Req3",
                qualified_name="Requirements::Req3",
                documentation="New requirement"
            )
        )

        old_reqs = req_list_v1
        new_reqs = req_list_v1 + [new_req]

        report = detector.detect_changes(old_reqs, new_reqs)

        assert len(report.added) == 1
        assert report.added[0] == "REQ-003"
        assert len(report.deleted) == 0
        assert len(report.modified) == 0
        assert report.total_changes == 1

    def test_detect_deleted_requirement(self, detector, req_list_v1):
        """Test detecting deleted requirements"""
        old_reqs = req_list_v1
        new_reqs = [req_list_v1[0]]  # Remove second requirement

        report = detector.detect_changes(old_reqs, new_reqs)

        assert len(report.added) == 0
        assert len(report.deleted) == 1
        assert report.deleted[0] == "REQ-002"
        assert len(report.modified) == 0
        assert report.total_changes == 1

    def test_detect_modified_requirement(self, detector, req_list_v1):
        """Test detecting modified requirements"""
        old_reqs = req_list_v1

        # Modify REQ-001
        modified_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-001",
                    name="Req1",
                    qualified_name="Requirements::Req1",
                    documentation="First requirement (updated)"
                ),
                attributes=[
                    RequirementAttribute(
                        name="height",
                        type="Integer",
                        min_value=140,  # Changed from 150
                        max_value=210   # Changed from 200
                    )
                ],
                constraints=[
                    Constraint(
                        type="require",
                        expression="140 <= height and height <= 210"
                    )
                ]
            ),
            req_list_v1[1]  # REQ-002 unchanged
        ]

        report = detector.detect_changes(old_reqs, modified_reqs)

        assert len(report.added) == 0
        assert len(report.deleted) == 0
        assert len(report.modified) == 1
        assert report.modified[0].requirement_id == "REQ-001"
        assert report.total_changes == 1

    def test_detect_multiple_changes(self, detector, req_list_v1):
        """Test detecting multiple types of changes"""
        old_reqs = req_list_v1

        # Add REQ-003, delete REQ-002, modify REQ-001
        new_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-001",
                    name="Req1",
                    qualified_name="Requirements::Req1",
                    documentation="Modified"
                ),
                attributes=[
                    RequirementAttribute(
                        name="height",
                        type="Integer",
                        min_value=100,
                        max_value=250
                    )
                ]
            ),
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-003",
                    name="Req3",
                    qualified_name="Requirements::Req3",
                    documentation="New requirement"
                )
            )
        ]

        report = detector.detect_changes(old_reqs, new_reqs)

        assert len(report.added) == 1
        assert "REQ-003" in report.added
        assert len(report.deleted) == 1
        assert "REQ-002" in report.deleted
        assert len(report.modified) == 1
        assert report.modified[0].requirement_id == "REQ-001"
        assert report.total_changes == 3


class TestChangeSeverity:
    """Tests for change severity classification - tested via detect_changes"""

    def test_minor_change_documentation_only(self, detector):
        """Test MINOR severity for documentation-only changes"""
        old_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test",
                documentation="Original text"
            )
        )]

        new_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test",
                documentation="Updated text"
            )
        )]

        report = detector.detect_changes(old_req, new_req)
        assert len(report.modified) == 1
        assert report.modified[0].severity == ChangeSeverity.MINOR

    def test_major_change_attribute_added(self, detector):
        """Test MAJOR severity for added attributes"""
        old_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test"
            ),
            attributes=[
                RequirementAttribute(name="value", type="Integer")
            ]
        )]

        new_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test"
            ),
            attributes=[
                RequirementAttribute(name="value", type="Integer"),
                RequirementAttribute(name="newValue", type="Real")  # Added
            ]
        )]

        report = detector.detect_changes(old_req, new_req)
        assert len(report.modified) == 1
        assert report.modified[0].severity == ChangeSeverity.MAJOR


class TestRequirementChange:
    """Tests for RequirementChange dataclass - tested indirectly via SyncDetector"""

    def test_change_from_detection(self, detector):
        """Test RequirementChange from actual detection"""
        old_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test",
                documentation="Original"
            )
        )]

        new_req = [Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="Test",
                qualified_name="Requirements::Test",
                documentation="Modified"
            )
        )]

        report = detector.detect_changes(old_req, new_req)
        assert len(report.modified) == 1

        change = report.modified[0]
        assert change.requirement_id == "REQ-001"
        assert change.change_type == ChangeType.MODIFIED

        # Test serialization
        change_dict = change.to_dict()
        assert change_dict['requirement_id'] == "REQ-001"
        assert change_dict['change_type'] == "MODIFIED"


class TestSyncReport:
    """Tests for SyncReport class"""

    def test_report_summary(self, detector, req_list_v1):
        """Test report summary generation"""
        # Create scenario: 1 added, 1 deleted, 1 modified
        old_reqs = req_list_v1
        new_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-001",
                    name="Req1",
                    qualified_name="Requirements::Req1",
                    documentation="Modified"
                ),
                attributes=[
                    RequirementAttribute(name="height", type="Integer", min_value=100, max_value=300)
                ]
            ),
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-003",
                    name="Req3",
                    qualified_name="Requirements::Req3",
                    documentation="New"
                )
            )
        ]

        report = detector.detect_changes(old_reqs, new_reqs)

        assert report.total_requirements == 2  # New requirements count
        assert report.total_changes == 3  # 1 added, 1 deleted, 1 modified
        assert len(report.added) == 1
        assert len(report.deleted) == 1
        assert len(report.modified) == 1

    def test_report_to_dict(self, detector, req_list_v1):
        """Test report serialization"""
        report = detector.detect_changes(req_list_v1, req_list_v1)
        report_dict = report.to_dict()

        assert 'total_requirements' in report_dict
        assert 'total_changes' in report_dict
        assert 'added' in report_dict
        assert 'deleted' in report_dict
        assert 'modified' in report_dict

    def test_report_to_markdown(self, detector, req_list_v1):
        """Test markdown report generation"""
        report = detector.detect_changes(req_list_v1, req_list_v1)
        markdown = report.to_markdown()

        assert "# Requirement Sync Report" in markdown
        assert "Total Requirements:" in markdown
        assert "Total Changes:" in markdown


class TestEdgeCases:
    """Test edge cases for change detection"""

    def test_empty_old_requirements(self, detector):
        """Test when old requirements list is empty (all new)"""
        new_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="REQ-001",
                    name="Req1",
                    qualified_name="Requirements::Req1"
                )
            )
        ]

        report = detector.detect_changes([], new_reqs)
        assert len(report.added) == 1
        assert len(report.deleted) == 0

    def test_empty_new_requirements(self, detector, req_list_v1):
        """Test when new requirements list is empty (all deleted)"""
        report = detector.detect_changes(req_list_v1, [])
        assert len(report.added) == 0
        assert len(report.deleted) == 2

    def test_both_empty(self, detector):
        """Test when both lists are empty"""
        report = detector.detect_changes([], [])
        assert report.total_changes == 0
        assert len(report.unchanged) == 0

    def test_requirement_without_id_uses_name(self, detector):
        """Test requirements without ID use name for identification"""
        old_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="TestReq",
                    name="TestReq",
                    qualified_name="Requirements::TestReq",
                    documentation="Original"
                )
            )
        ]

        new_reqs = [
            Requirement(
                metadata=RequirementMetadata(
                    id="TestReq",
                    name="TestReq",
                    qualified_name="Requirements::TestReq",
                    documentation="Modified"
                )
            )
        ]

        report = detector.detect_changes(old_reqs, new_reqs)
        assert len(report.modified) == 1
        assert report.modified[0].requirement_id == "TestReq"
