"""
Sync detection engine

Compares old and new requirements to detect changes
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime

from ..extractor.models import Requirement
from .fingerprint import (
    RequirementFingerprint,
    create_fingerprint,
    compare_fingerprints,
)

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Type of requirement change"""
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ChangeSeverity(str, Enum):
    """Severity of requirement change"""
    NONE = "none"          # No change
    MINOR = "minor"        # Documentation/name only
    MODERATE = "moderate"  # Attribute bounds, minor constraint changes
    MAJOR = "major"        # Structure change, new attributes, constraint logic change


@dataclass
class RequirementChange:
    """Details of a requirement change"""

    requirement_id: str
    change_type: ChangeType
    severity: ChangeSeverity
    old_fingerprint: Optional[RequirementFingerprint]
    new_fingerprint: Optional[RequirementFingerprint]
    old_requirement: Optional[Requirement]
    new_requirement: Optional[Requirement]
    change_details: Dict[str, any] = field(default_factory=dict)

    @property
    def has_content_change(self) -> bool:
        """Check if content actually changed"""
        return self.change_type in [ChangeType.ADDED, ChangeType.DELETED, ChangeType.MODIFIED]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "requirement_id": self.requirement_id,
            "change_type": self.change_type.value,
            "severity": self.severity.value,
            "old_hash": self.old_fingerprint.content_hash if self.old_fingerprint else None,
            "new_hash": self.new_fingerprint.content_hash if self.new_fingerprint else None,
            "change_details": self.change_details,
        }


@dataclass
class SyncReport:
    """Report of synchronization analysis"""

    timestamp: datetime
    added: List[RequirementChange] = field(default_factory=list)
    deleted: List[RequirementChange] = field(default_factory=list)
    modified: List[RequirementChange] = field(default_factory=list)
    unchanged: List[RequirementChange] = field(default_factory=list)

    @property
    def total_requirements(self) -> int:
        """Total number of requirements analyzed"""
        return len(self.added) + len(self.deleted) + len(self.modified) + len(self.unchanged)

    @property
    def total_changes(self) -> int:
        """Total number of changes detected"""
        return len(self.added) + len(self.deleted) + len(self.modified)

    @property
    def has_changes(self) -> bool:
        """Check if any changes detected"""
        return self.total_changes > 0

    def get_by_severity(self, severity: ChangeSeverity) -> List[RequirementChange]:
        """Get all changes with specific severity"""
        return [
            change for change in (self.added + self.deleted + self.modified)
            if change.severity == severity
        ]

    def print_summary(self):
        """Print human-readable summary"""
        print("=" * 70)
        print("Requirement Sync Report")
        print("=" * 70)
        print(f"Generated: {self.timestamp.isoformat()}")
        print()
        print(f"Total Requirements: {self.total_requirements}")
        print(f"Total Changes:      {self.total_changes}")
        print()
        print(f"  Added:      {len(self.added)}")
        print(f"  Deleted:    {len(self.deleted)}")
        print(f"  Modified:   {len(self.modified)}")
        print(f"  Unchanged:  {len(self.unchanged)}")
        print()

        if self.modified:
            print("Modified Requirements by Severity:")
            for severity in [ChangeSeverity.MAJOR, ChangeSeverity.MODERATE, ChangeSeverity.MINOR]:
                changes = [c for c in self.modified if c.severity == severity]
                if changes:
                    print(f"  {severity.value.upper()}: {len(changes)}")
                    for change in changes[:5]:  # Show first 5
                        print(f"    - {change.requirement_id}")
                    if len(changes) > 5:
                        print(f"    ... and {len(changes) - 5} more")
        print("=" * 70)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total_requirements": self.total_requirements,
                "total_changes": self.total_changes,
                "added": len(self.added),
                "deleted": len(self.deleted),
                "modified": len(self.modified),
                "unchanged": len(self.unchanged),
            },
            "changes": {
                "added": [c.to_dict() for c in self.added],
                "deleted": [c.to_dict() for c in self.deleted],
                "modified": [c.to_dict() for c in self.modified],
            }
        }


class SyncDetector:
    """Detects changes between requirement sets"""

    def __init__(self):
        """Initialize sync detector"""
        pass

    def detect_changes(
        self,
        old_requirements: List[Requirement],
        new_requirements: List[Requirement],
        old_fingerprints: Optional[Dict[str, RequirementFingerprint]] = None
    ) -> SyncReport:
        """
        Detect changes between old and new requirement sets

        Args:
            old_requirements: Previous requirement set
            new_requirements: New requirement set
            old_fingerprints: Optional cached fingerprints for old requirements

        Returns:
            SyncReport with detected changes
        """
        logger.info("Detecting requirement changes...")

        # Create lookup dictionaries
        old_by_id = {r.metadata.id: r for r in old_requirements}
        new_by_id = {r.metadata.id: r for r in new_requirements}

        # Create fingerprints
        if old_fingerprints is None:
            old_fingerprints = {
                req.metadata.id: create_fingerprint(req)
                for req in old_requirements
            }

        new_fingerprints = {
            req.metadata.id: create_fingerprint(req)
            for req in new_requirements
        }

        # Find changes
        old_ids = set(old_by_id.keys())
        new_ids = set(new_by_id.keys())

        added = self._find_added(new_ids - old_ids, new_by_id, new_fingerprints)
        deleted = self._find_deleted(old_ids - new_ids, old_by_id, old_fingerprints)
        modified = self._find_modified(
            old_ids & new_ids,
            old_by_id, new_by_id,
            old_fingerprints, new_fingerprints
        )
        unchanged = self._find_unchanged(
            old_ids & new_ids,
            old_by_id, new_by_id,
            old_fingerprints, new_fingerprints
        )

        logger.info(f"Detected {len(added)} added, {len(deleted)} deleted, "
                   f"{len(modified)} modified, {len(unchanged)} unchanged")

        return SyncReport(
            timestamp=datetime.now(),
            added=added,
            deleted=deleted,
            modified=modified,
            unchanged=unchanged,
        )

    def _find_added(
        self,
        added_ids: Set[str],
        new_by_id: Dict[str, Requirement],
        new_fingerprints: Dict[str, RequirementFingerprint]
    ) -> List[RequirementChange]:
        """Find added requirements"""
        return [
            RequirementChange(
                requirement_id=req_id,
                change_type=ChangeType.ADDED,
                severity=ChangeSeverity.MAJOR,  # New requirements are always major
                old_fingerprint=None,
                new_fingerprint=new_fingerprints[req_id],
                old_requirement=None,
                new_requirement=new_by_id[req_id],
                change_details={"reason": "New requirement"},
            )
            for req_id in sorted(added_ids)
        ]

    def _find_deleted(
        self,
        deleted_ids: Set[str],
        old_by_id: Dict[str, Requirement],
        old_fingerprints: Dict[str, RequirementFingerprint]
    ) -> List[RequirementChange]:
        """Find deleted requirements"""
        return [
            RequirementChange(
                requirement_id=req_id,
                change_type=ChangeType.DELETED,
                severity=ChangeSeverity.MAJOR,  # Deletions are always major
                old_fingerprint=old_fingerprints[req_id],
                new_fingerprint=None,
                old_requirement=old_by_id[req_id],
                new_requirement=None,
                change_details={"reason": "Requirement deleted"},
            )
            for req_id in sorted(deleted_ids)
        ]

    def _find_modified(
        self,
        common_ids: Set[str],
        old_by_id: Dict[str, Requirement],
        new_by_id: Dict[str, Requirement],
        old_fingerprints: Dict[str, RequirementFingerprint],
        new_fingerprints: Dict[str, RequirementFingerprint]
    ) -> List[RequirementChange]:
        """Find modified requirements"""
        modified = []

        for req_id in sorted(common_ids):
            old_fp = old_fingerprints[req_id]
            new_fp = new_fingerprints[req_id]

            # Check if content changed
            if old_fp.content_hash != new_fp.content_hash:
                comparison = compare_fingerprints(old_fp, new_fp)
                severity = self._determine_severity(
                    old_by_id[req_id],
                    new_by_id[req_id],
                    comparison
                )

                change_details = self._analyze_change_details(
                    old_by_id[req_id],
                    new_by_id[req_id]
                )

                modified.append(RequirementChange(
                    requirement_id=req_id,
                    change_type=ChangeType.MODIFIED,
                    severity=severity,
                    old_fingerprint=old_fp,
                    new_fingerprint=new_fp,
                    old_requirement=old_by_id[req_id],
                    new_requirement=new_by_id[req_id],
                    change_details=change_details,
                ))

        return modified

    def _find_unchanged(
        self,
        common_ids: Set[str],
        old_by_id: Dict[str, Requirement],
        new_by_id: Dict[str, Requirement],
        old_fingerprints: Dict[str, RequirementFingerprint],
        new_fingerprints: Dict[str, RequirementFingerprint]
    ) -> List[RequirementChange]:
        """Find unchanged requirements"""
        unchanged = []

        for req_id in sorted(common_ids):
            if old_fingerprints[req_id].content_hash == new_fingerprints[req_id].content_hash:
                unchanged.append(RequirementChange(
                    requirement_id=req_id,
                    change_type=ChangeType.UNCHANGED,
                    severity=ChangeSeverity.NONE,
                    old_fingerprint=old_fingerprints[req_id],
                    new_fingerprint=new_fingerprints[req_id],
                    old_requirement=old_by_id[req_id],
                    new_requirement=new_by_id[req_id],
                ))

        return unchanged

    def _determine_severity(
        self,
        old_req: Requirement,
        new_req: Requirement,
        comparison: Dict[str, bool]
    ) -> ChangeSeverity:
        """Determine severity of change"""

        # Only metadata changed (documentation, name)
        if comparison["metadata_only"]:
            return ChangeSeverity.MINOR

        # Structure changed (attributes, constraints)
        if comparison["structure_changed"]:
            # Check if it's a major structural change
            old_attrs = {a.name for a in old_req.attributes}
            new_attrs = {a.name for a in new_req.attributes}

            # Attributes added or removed
            if old_attrs != new_attrs:
                return ChangeSeverity.MAJOR

            # Constraint count changed
            if len(old_req.constraints) != len(new_req.constraints):
                return ChangeSeverity.MAJOR

            # Otherwise moderate (bounds changed, etc.)
            return ChangeSeverity.MODERATE

        return ChangeSeverity.MODERATE

    def _analyze_change_details(
        self,
        old_req: Requirement,
        new_req: Requirement
    ) -> Dict[str, any]:
        """Analyze what specifically changed"""
        details = {}

        # Documentation changes
        if old_req.metadata.documentation != new_req.metadata.documentation:
            details["documentation_changed"] = True

        # Name changes
        if old_req.metadata.name != new_req.metadata.name:
            details["name_changed"] = True
            details["old_name"] = old_req.metadata.name
            details["new_name"] = new_req.metadata.name

        # Attribute changes
        old_attrs = {a.name: a for a in old_req.attributes}
        new_attrs = {a.name: a for a in new_req.attributes}

        added_attrs = set(new_attrs.keys()) - set(old_attrs.keys())
        removed_attrs = set(old_attrs.keys()) - set(new_attrs.keys())

        if added_attrs:
            details["attributes_added"] = list(added_attrs)
        if removed_attrs:
            details["attributes_removed"] = list(removed_attrs)

        # Check for attribute modifications
        modified_attrs = []
        for attr_name in set(old_attrs.keys()) & set(new_attrs.keys()):
            old_attr = old_attrs[attr_name]
            new_attr = new_attrs[attr_name]

            if (old_attr.type != new_attr.type or
                old_attr.min_value != new_attr.min_value or
                old_attr.max_value != new_attr.max_value):
                modified_attrs.append(attr_name)

        if modified_attrs:
            details["attributes_modified"] = modified_attrs

        # Constraint changes
        old_constraints = [c.expression for c in old_req.constraints]
        new_constraints = [c.expression for c in new_req.constraints]

        if old_constraints != new_constraints:
            details["constraints_changed"] = True
            details["constraint_count_old"] = len(old_constraints)
            details["constraint_count_new"] = len(new_constraints)

        return details
