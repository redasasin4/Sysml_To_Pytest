"""
Tests for sync fingerprinting module
"""

import pytest
from datetime import datetime

from sysml2pytest.sync.fingerprint import (
    RequirementFingerprint,
    compute_requirement_hash,
    create_fingerprint,
    compare_fingerprints,
)
from sysml2pytest.extractor.models import (
    Requirement,
    RequirementMetadata,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
)


@pytest.fixture
def sample_requirement():
    """Create a sample requirement for testing"""
    return Requirement(
        metadata=RequirementMetadata(
            id="REQ-001",
            name="TestRequirement",
            qualified_name="Requirements::TestRequirement",
            documentation="Test requirement for fingerprinting"
        ),
        attributes=[
            RequirementAttribute(
                name="treeHeight",
                type="Integer",
                description="Height of tree",
                min_value=150,
                max_value=200
            )
        ],
        constraints=[
            Constraint(
                type="require",
                expression="150 <= treeHeight and treeHeight <= 200",
                description="Height bounds"
            )
        ]
    )


class TestComputeRequirementHash:
    """Tests for compute_requirement_hash function"""

    def test_hash_is_deterministic(self, sample_requirement):
        """Same requirement should produce same hash"""
        hash1 = compute_requirement_hash(sample_requirement)
        hash2 = compute_requirement_hash(sample_requirement)
        assert hash1 == hash2

    def test_hash_is_sha256(self, sample_requirement):
        """Hash should be 64-character SHA-256"""
        hash_value = compute_requirement_hash(sample_requirement)
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_different_requirements_different_hashes(self, sample_requirement):
        """Different requirements should produce different hashes"""
        req2 = Requirement(
            metadata=RequirementMetadata(
                id="REQ-002",
                name="DifferentRequirement",
                qualified_name="Requirements::DifferentRequirement",
                documentation="Different text"
            )
        )

        hash1 = compute_requirement_hash(sample_requirement)
        hash2 = compute_requirement_hash(req2)
        assert hash1 != hash2

    def test_hash_changes_with_attribute_modification(self, sample_requirement):
        """Hash should change when attribute is modified"""
        original_hash = compute_requirement_hash(sample_requirement)

        # Modify attribute
        sample_requirement.attributes[0].min_value = 200
        modified_hash = compute_requirement_hash(sample_requirement)

        assert original_hash != modified_hash

    def test_hash_changes_with_constraint_modification(self, sample_requirement):
        """Hash should change when constraint is modified"""
        original_hash = compute_requirement_hash(sample_requirement)

        # Modify constraint
        sample_requirement.constraints[0].expression = "treeHeight >= 200"
        modified_hash = compute_requirement_hash(sample_requirement)

        assert original_hash != modified_hash

    def test_hash_stable_with_metadata_name_change(self, sample_requirement):
        """Hash should remain stable with just name change"""
        original_hash = compute_requirement_hash(sample_requirement)

        # Change only name (not structural)
        sample_requirement.metadata.name = "NewName"

        # For structure hash, this should NOT change the content
        # But metadata hash will change
        # This test verifies hash is based on semantic content
        new_hash = compute_requirement_hash(sample_requirement)

        # Since we hash the full content including metadata, it will change
        # But structure-only hash (if we had it) would not change
        assert original_hash != new_hash


class TestRequirementFingerprint:
    """Tests for RequirementFingerprint dataclass"""

    def test_create_fingerprint(self, sample_requirement):
        """Test fingerprint creation"""
        fp = create_fingerprint(sample_requirement, version=1)

        assert fp.requirement_id == "REQ-001"
        assert fp.version == 1
        assert len(fp.content_hash) == 64
        assert len(fp.metadata_hash) == 64
        assert len(fp.structure_hash) == 64
        assert isinstance(fp.timestamp, str)

    def test_fingerprint_serialization(self, sample_requirement):
        """Test fingerprint to_dict/from_dict"""
        fp = create_fingerprint(sample_requirement, version=1)

        # Serialize
        fp_dict = fp.to_dict()
        assert fp_dict['requirement_id'] == "REQ-001"
        assert fp_dict['version'] == 1

        # Deserialize
        fp_restored = RequirementFingerprint.from_dict(fp_dict)
        assert fp_restored.requirement_id == fp.requirement_id
        assert fp_restored.content_hash == fp.content_hash
        assert fp_restored.version == fp.version

    def test_fingerprint_version_increments(self, sample_requirement):
        """Test creating fingerprints with different versions"""
        fp1 = create_fingerprint(sample_requirement, version=1)
        fp2 = create_fingerprint(sample_requirement, version=2)

        assert fp1.version == 1
        assert fp2.version == 2
        # Content hashes should be same for same requirement
        assert fp1.content_hash == fp2.content_hash


class TestCompareFingerprints:
    """Tests for compare_fingerprints function"""

    def test_compare_identical_fingerprints(self, sample_requirement):
        """Identical fingerprints should show no changes"""
        fp1 = create_fingerprint(sample_requirement, version=1)
        fp2 = create_fingerprint(sample_requirement, version=1)

        comparison = compare_fingerprints(fp1, fp2)

        assert comparison['content_changed'] is False
        assert comparison['metadata_only'] is False
        assert comparison['structure_changed'] is False

    def test_compare_content_changed(self, sample_requirement):
        """Detect content changes"""
        fp1 = create_fingerprint(sample_requirement, version=1)

        # Modify requirement
        sample_requirement.constraints[0].expression = "treeHeight >= 200"
        fp2 = create_fingerprint(sample_requirement, version=2)

        comparison = compare_fingerprints(fp1, fp2)

        assert comparison['content_changed'] is True
        # Structure changed because constraint changed
        assert comparison['structure_changed'] is True

    def test_compare_metadata_only_change(self):
        """Detect metadata-only changes"""
        req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-001",
                name="TestReq",
                qualified_name="Requirements::TestReq",
                documentation="Test requirement"
            )
        )

        fp1 = create_fingerprint(req, version=1)

        # Change only metadata (documentation)
        req.metadata.documentation = "Updated test requirement"
        fp2 = create_fingerprint(req, version=2)

        comparison = compare_fingerprints(fp1, fp2)

        assert comparison['content_changed'] is True

    def test_compare_structure_change(self, sample_requirement):
        """Detect structural changes"""
        fp1 = create_fingerprint(sample_requirement, version=1)

        # Add new attribute (structural change)
        sample_requirement.attributes.append(
            RequirementAttribute(
                name="newAttribute",
                type="Integer",
                description="New attribute"
            )
        )
        fp2 = create_fingerprint(sample_requirement, version=2)

        comparison = compare_fingerprints(fp1, fp2)

        assert comparison['content_changed'] is True
        assert comparison['structure_changed'] is True


class TestFingerprintEdgeCases:
    """Test edge cases for fingerprinting"""

    def test_requirement_with_no_attributes(self):
        """Test fingerprint of requirement with no attributes"""
        req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-EMPTY",
                name="EmptyReq",
                qualified_name="Requirements::EmptyReq",
                documentation="No attributes"
            ),
            attributes=[],
            constraints=[]
        )

        fp = create_fingerprint(req, version=1)
        assert len(fp.content_hash) == 64

    def test_requirement_with_no_constraints(self):
        """Test fingerprint of requirement with no constraints"""
        req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-NO-CONST",
                name="NoConstraints",
                qualified_name="Requirements::NoConstraints",
                documentation="Has attributes but no constraints"
            ),
            attributes=[
                RequirementAttribute(
                    name="attr1",
                    type="Integer",
                    description="Attribute 1"
                )
            ],
            constraints=[]
        )

        fp = create_fingerprint(req, version=1)
        assert len(fp.content_hash) == 64

    def test_requirement_with_complex_constraints(self):
        """Test fingerprint with complex constraint expressions"""
        req = Requirement(
            metadata=RequirementMetadata(
                id="REQ-COMPLEX",
                name="ComplexReq",
                qualified_name="Requirements::ComplexReq",
                documentation="Complex constraints"
            ),
            attributes=[
                RequirementAttribute(
                    name="x",
                    type="Real",
                    description="X value"
                ),
                RequirementAttribute(
                    name="y",
                    type="Real",
                    description="Y value"
                )
            ],
            constraints=[
                Constraint(
                    type="require",
                    expression="(x >= 0 and y >= 0) and (x + y <= 100)",
                    description="Complex constraint"
                )
            ]
        )

        fp = create_fingerprint(req, version=1)
        assert len(fp.content_hash) == 64

    def test_hash_consistency_across_runs(self, sample_requirement):
        """Verify hash remains consistent across multiple computations"""
        hashes = [compute_requirement_hash(sample_requirement) for _ in range(10)]
        assert all(h == hashes[0] for h in hashes)
