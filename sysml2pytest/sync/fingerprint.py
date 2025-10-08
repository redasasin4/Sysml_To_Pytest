"""
Requirement fingerprinting for change detection

Generates content-based hashes to detect requirement changes
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

from ..extractor.models import Requirement, AttributeType


@dataclass
class RequirementFingerprint:
    """Fingerprint of a requirement for change detection"""

    requirement_id: str
    content_hash: str
    version: int
    timestamp: datetime
    metadata_hash: str  # Hash of just metadata (for minor change detection)
    structure_hash: str  # Hash of attributes/constraints (for major change detection)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "requirement_id": self.requirement_id,
            "content_hash": self.content_hash,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "metadata_hash": self.metadata_hash,
            "structure_hash": self.structure_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementFingerprint":
        """Create from dictionary"""
        return cls(
            requirement_id=data["requirement_id"],
            content_hash=data["content_hash"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata_hash=data["metadata_hash"],
            structure_hash=data["structure_hash"],
        )


def compute_requirement_hash(requirement: Requirement) -> str:
    """
    Compute deterministic content-based hash of requirement

    Includes all semantic content that affects generated tests:
    - Attributes (names, types, bounds)
    - Constraints (kind, expressions)
    - Documentation

    Excludes:
    - Requirement ID (may change in refactoring)
    - Timestamps
    - Source location
    - Stakeholders (don't affect tests)

    Args:
        requirement: Requirement to hash

    Returns:
        SHA-256 hex digest of requirement content
    """
    content = _extract_semantic_content(requirement)
    content_json = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content_json.encode()).hexdigest()


def compute_metadata_hash(requirement: Requirement) -> str:
    """
    Compute hash of only metadata (documentation, names)

    Used to detect minor changes that don't affect test logic

    Args:
        requirement: Requirement to hash

    Returns:
        SHA-256 hex digest of metadata
    """
    metadata = {
        "name": requirement.metadata.name,
        "documentation": requirement.metadata.documentation or "",
    }
    content_json = json.dumps(metadata, sort_keys=True)
    return hashlib.sha256(content_json.encode()).hexdigest()


def compute_structure_hash(requirement: Requirement) -> str:
    """
    Compute hash of structure (attributes and constraints)

    Used to detect major changes that require test regeneration

    Args:
        requirement: Requirement to hash

    Returns:
        SHA-256 hex digest of structure
    """
    structure = {
        "attributes": sorted([
            {
                "name": attr.name,
                "type": attr.type.value,
                "min_value": attr.min_value,
                "max_value": attr.max_value,
            }
            for attr in requirement.attributes
        ], key=lambda x: x["name"]),
        "constraints": sorted([
            {
                "kind": c.kind.value,
                "expression": c.expression,
            }
            for c in requirement.constraints
        ], key=lambda x: (x["kind"], x["expression"])),
    }
    content_json = json.dumps(structure, sort_keys=True, default=str)
    return hashlib.sha256(content_json.encode()).hexdigest()


def create_fingerprint(
    requirement: Requirement,
    version: int = 1,
    timestamp: datetime = None
) -> RequirementFingerprint:
    """
    Create complete fingerprint for a requirement

    Args:
        requirement: Requirement to fingerprint
        version: Version number (default: 1)
        timestamp: Timestamp (default: now)

    Returns:
        RequirementFingerprint
    """
    if timestamp is None:
        timestamp = datetime.now()

    return RequirementFingerprint(
        requirement_id=requirement.metadata.id,
        content_hash=compute_requirement_hash(requirement),
        version=version,
        timestamp=timestamp,
        metadata_hash=compute_metadata_hash(requirement),
        structure_hash=compute_structure_hash(requirement),
    )


def _extract_semantic_content(requirement: Requirement) -> Dict[str, Any]:
    """Extract semantic content for hashing"""
    return {
        "name": requirement.metadata.name,
        "documentation": requirement.metadata.documentation or "",
        "attributes": sorted([
            {
                "name": attr.name,
                "type": attr.type.value,
                "min_value": attr.min_value,
                "max_value": attr.max_value,
                "description": attr.description or "",
            }
            for attr in requirement.attributes
        ], key=lambda x: x["name"]),
        "constraints": sorted([
            {
                "kind": c.kind.value,
                "expression": c.expression,
                "description": c.description or "",
            }
            for c in requirement.constraints
        ], key=lambda x: (x["kind"], x["expression"])),
        "nested_requirements": sorted(requirement.nested_requirements),
    }


def compare_fingerprints(
    old: RequirementFingerprint,
    new: RequirementFingerprint
) -> Dict[str, bool]:
    """
    Compare two fingerprints to determine what changed

    Returns:
        Dict with change indicators:
        - content_changed: Any content changed
        - metadata_only: Only metadata changed (minor)
        - structure_changed: Structure changed (major)
    """
    return {
        "content_changed": old.content_hash != new.content_hash,
        "metadata_only": (
            old.content_hash != new.content_hash and
            old.structure_hash == new.structure_hash
        ),
        "structure_changed": old.structure_hash != new.structure_hash,
    }
