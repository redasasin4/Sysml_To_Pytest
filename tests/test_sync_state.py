"""
Tests for sync state management module
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from sysml2pytest.sync.state import (
    RequirementState,
    TestFileState,
    SyncState,
    SyncStateManager,
)
from sysml2pytest.sync.fingerprint import RequirementFingerprint


@pytest.fixture
def temp_state_dir():
    """Create temporary directory for state files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_requirement_state():
    """Create sample RequirementState"""
    return RequirementState(
        requirement_id="REQ-001",
        content_hash="abc123",
        version=1,
        test_file=Path("tests/test_req001.py"),
        last_updated=datetime(2025, 10, 7, 12, 0, 0),
        has_custom_code=False
    )


@pytest.fixture
def sample_test_file_state():
    """Create sample TestFileState"""
    return TestFileState(
        file_path=Path("tests/test_requirements.py"),
        requirements=["REQ-001", "REQ-002"],
        last_generated=datetime(2025, 10, 7, 12, 0, 0),
        has_custom_code=True,
        backup_count=3
    )


class TestRequirementState:
    """Tests for RequirementState dataclass"""

    def test_requirement_state_creation(self, sample_requirement_state):
        """Test creating RequirementState"""
        assert sample_requirement_state.requirement_id == "REQ-001"
        assert sample_requirement_state.content_hash == "abc123"
        assert sample_requirement_state.version == 1
        assert sample_requirement_state.has_custom_code is False

    def test_requirement_state_to_dict(self, sample_requirement_state):
        """Test RequirementState serialization"""
        state_dict = sample_requirement_state.to_dict()

        assert state_dict['requirement_id'] == "REQ-001"
        assert state_dict['content_hash'] == "abc123"
        assert state_dict['version'] == 1
        assert state_dict['test_file'] == "tests/test_req001.py"
        assert state_dict['has_custom_code'] is False

    def test_requirement_state_from_dict(self, sample_requirement_state):
        """Test RequirementState deserialization"""
        state_dict = sample_requirement_state.to_dict()
        restored = RequirementState.from_dict(state_dict)

        assert restored.requirement_id == sample_requirement_state.requirement_id
        assert restored.content_hash == sample_requirement_state.content_hash
        assert restored.version == sample_requirement_state.version
        assert restored.test_file == sample_requirement_state.test_file

    def test_requirement_state_with_fingerprint(self):
        """Test RequirementState with fingerprint"""
        fp = RequirementFingerprint(
            requirement_id="REQ-001",
            content_hash="abc",
            metadata_hash="def",
            structure_hash="ghi",
            version=1,
            timestamp=datetime(2025, 10, 7, 12, 0, 0)
        )

        state = RequirementState(
            requirement_id="REQ-001",
            content_hash="abc",
            version=1,
            test_file=None,
            last_updated=datetime.now(),
            fingerprint=fp
        )

        state_dict = state.to_dict()
        assert state_dict['fingerprint'] is not None
        assert state_dict['fingerprint']['content_hash'] == "abc"

        # Deserialize
        restored = RequirementState.from_dict(state_dict)
        assert restored.fingerprint is not None
        assert restored.fingerprint.content_hash == "abc"


class TestTestFileState:
    """Tests for TestFileState dataclass"""

    def test_test_file_state_creation(self, sample_test_file_state):
        """Test creating TestFileState"""
        assert sample_test_file_state.file_path == Path("tests/test_requirements.py")
        assert len(sample_test_file_state.requirements) == 2
        assert sample_test_file_state.has_custom_code is True
        assert sample_test_file_state.backup_count == 3

    def test_test_file_state_to_dict(self, sample_test_file_state):
        """Test TestFileState serialization"""
        state_dict = sample_test_file_state.to_dict()

        assert state_dict['file_path'] == "tests/test_requirements.py"
        assert state_dict['requirements'] == ["REQ-001", "REQ-002"]
        assert state_dict['has_custom_code'] is True
        assert state_dict['backup_count'] == 3

    def test_test_file_state_from_dict(self, sample_test_file_state):
        """Test TestFileState deserialization"""
        state_dict = sample_test_file_state.to_dict()
        restored = TestFileState.from_dict(state_dict)

        assert restored.file_path == sample_test_file_state.file_path
        assert restored.requirements == sample_test_file_state.requirements
        assert restored.has_custom_code == sample_test_file_state.has_custom_code


class TestSyncState:
    """Tests for SyncState dataclass"""

    def test_sync_state_creation(self):
        """Test creating empty SyncState"""
        state = SyncState()

        assert state.last_sync is None
        assert state.sync_count == 0
        assert len(state.requirements) == 0
        assert len(state.test_files) == 0

    def test_add_requirement(self, sample_requirement_state):
        """Test adding requirement to state"""
        state = SyncState()
        state.add_requirement(sample_requirement_state)

        assert len(state.requirements) == 1
        assert "REQ-001" in state.requirements
        assert state.requirements["REQ-001"].content_hash == "abc123"

    def test_get_requirement(self, sample_requirement_state):
        """Test getting requirement from state"""
        state = SyncState()
        state.add_requirement(sample_requirement_state)

        req = state.get_requirement("REQ-001")
        assert req is not None
        assert req.requirement_id == "REQ-001"

        # Non-existent requirement
        req = state.get_requirement("REQ-999")
        assert req is None

    def test_remove_requirement(self, sample_requirement_state):
        """Test removing requirement from state"""
        state = SyncState()
        state.add_requirement(sample_requirement_state)
        assert len(state.requirements) == 1

        state.remove_requirement("REQ-001")
        assert len(state.requirements) == 0

    def test_add_test_file(self, sample_test_file_state):
        """Test adding test file to state"""
        state = SyncState()
        state.add_test_file(sample_test_file_state)

        assert len(state.test_files) == 1
        key = str(sample_test_file_state.file_path)
        assert key in state.test_files

    def test_get_test_file(self, sample_test_file_state):
        """Test getting test file from state"""
        state = SyncState()
        state.add_test_file(sample_test_file_state)

        test_file = state.get_test_file(Path("tests/test_requirements.py"))
        assert test_file is not None
        assert len(test_file.requirements) == 2

    def test_get_requirements_in_file(self, sample_test_file_state):
        """Test getting requirements in a file"""
        state = SyncState()
        state.add_test_file(sample_test_file_state)

        reqs = state.get_requirements_in_file(Path("tests/test_requirements.py"))
        assert reqs == ["REQ-001", "REQ-002"]

        # Non-existent file
        reqs = state.get_requirements_in_file(Path("tests/nonexistent.py"))
        assert reqs == []

    def test_get_files_for_requirement(self, sample_test_file_state):
        """Test getting files containing a requirement"""
        state = SyncState()
        state.add_test_file(sample_test_file_state)

        # Add another file with REQ-001
        another_file = TestFileState(
            file_path=Path("tests/test_other.py"),
            requirements=["REQ-001", "REQ-003"],
            last_generated=datetime.now()
        )
        state.add_test_file(another_file)

        files = state.get_files_for_requirement("REQ-001")
        assert len(files) == 2

        files = state.get_files_for_requirement("REQ-002")
        assert len(files) == 1

    def test_sync_state_serialization(self, sample_requirement_state, sample_test_file_state):
        """Test SyncState to_dict/from_dict"""
        state = SyncState(
            last_sync=datetime(2025, 10, 7, 12, 0, 0),
            sync_count=5
        )
        state.add_requirement(sample_requirement_state)
        state.add_test_file(sample_test_file_state)

        # Serialize
        state_dict = state.to_dict()
        assert state_dict['sync_count'] == 5
        assert 'last_sync' in state_dict
        assert 'requirements' in state_dict
        assert 'test_files' in state_dict

        # Deserialize
        restored = SyncState.from_dict(state_dict)
        assert restored.sync_count == 5
        assert len(restored.requirements) == 1
        assert len(restored.test_files) == 1


class TestSyncStateManager:
    """Tests for SyncStateManager class"""

    def test_state_manager_creation(self, temp_state_dir):
        """Test creating SyncStateManager"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        assert manager.state_dir == temp_state_dir
        assert manager.state_file == temp_state_dir / "sync_state.json"

    def test_initialize_creates_directory(self, temp_state_dir):
        """Test initialize creates state directory"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        assert temp_state_dir.exists()
        assert manager.state_file.exists()
        assert manager.state is not None

    def test_save_and_load_state(self, temp_state_dir, sample_requirement_state):
        """Test saving and loading state"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        # Add requirement
        manager.state.add_requirement(sample_requirement_state)
        manager.save()

        # Create new manager and load
        manager2 = SyncStateManager(state_dir=temp_state_dir)
        manager2.load()

        assert len(manager2.state.requirements) == 1
        assert "REQ-001" in manager2.state.requirements

    def test_update_requirement(self, temp_state_dir):
        """Test updating requirement state"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        manager.update_requirement(
            requirement_id="REQ-001",
            content_hash="abc123",
            version=1,
            test_file=Path("tests/test_req001.py"),
            has_custom_code=True
        )

        req = manager.state.get_requirement("REQ-001")
        assert req is not None
        assert req.version == 1
        assert req.has_custom_code is True

    def test_update_test_file(self, temp_state_dir):
        """Test updating test file state"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        manager.update_test_file(
            file_path=Path("tests/test_requirements.py"),
            requirements=["REQ-001", "REQ-002"],
            has_custom_code=True
        )

        test_file = manager.state.get_test_file(Path("tests/test_requirements.py"))
        assert test_file is not None
        assert len(test_file.requirements) == 2

    def test_mark_synced(self, temp_state_dir):
        """Test marking sync as completed"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        initial_count = manager.state.sync_count
        manager.mark_synced()

        assert manager.state.last_sync is not None
        assert manager.state.sync_count == initial_count + 1

    def test_get_requirement_version(self, temp_state_dir):
        """Test getting requirement version"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        # Non-existent requirement
        version = manager.get_requirement_version("REQ-999")
        assert version == 0

        # Add requirement
        manager.update_requirement(
            requirement_id="REQ-001",
            content_hash="abc",
            version=3,
            test_file=None
        )

        version = manager.get_requirement_version("REQ-001")
        assert version == 3

    def test_has_requirement(self, temp_state_dir):
        """Test checking if requirement exists"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        assert manager.has_requirement("REQ-001") is False

        manager.update_requirement(
            requirement_id="REQ-001",
            content_hash="abc",
            version=1,
            test_file=None
        )

        assert manager.has_requirement("REQ-001") is True

    def test_get_all_requirements(self, temp_state_dir):
        """Test getting all requirements"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        manager.update_requirement("REQ-001", "abc", 1, None)
        manager.update_requirement("REQ-002", "def", 1, None)

        all_reqs = manager.get_all_requirements()
        assert len(all_reqs) == 2

    def test_get_stale_requirements(self, temp_state_dir):
        """Test detecting stale requirements"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        manager.update_requirement("REQ-001", "abc", 1, None)
        manager.update_requirement("REQ-002", "def", 1, None)
        manager.update_requirement("REQ-003", "ghi", 1, None)

        # Current IDs don't include REQ-002
        current_ids = {"REQ-001", "REQ-003"}
        stale = manager.get_stale_requirements(current_ids)

        assert len(stale) == 1
        assert "REQ-002" in stale

    def test_cleanup_stale_requirements(self, temp_state_dir):
        """Test cleaning up stale requirements"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        manager.update_requirement("REQ-001", "abc", 1, None)
        manager.update_requirement("REQ-002", "def", 1, None)
        manager.save()

        # Cleanup REQ-002
        current_ids = {"REQ-001"}
        manager.cleanup_stale_requirements(current_ids)

        assert manager.has_requirement("REQ-001") is True
        assert manager.has_requirement("REQ-002") is False


class TestStateManagerEdgeCases:
    """Test edge cases for state manager"""

    def test_load_nonexistent_file(self, temp_state_dir):
        """Test loading when state file doesn't exist"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        state = manager.load()

        assert state is not None
        assert len(state.requirements) == 0

    def test_load_corrupted_file(self, temp_state_dir):
        """Test loading corrupted state file"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        # Corrupt the file
        with open(manager.state_file, 'w') as f:
            f.write("{ invalid json")

        # Load should handle gracefully
        state = manager.load()
        assert state is not None

    def test_multiple_sync_cycles(self, temp_state_dir):
        """Test multiple sync cycles"""
        manager = SyncStateManager(state_dir=temp_state_dir)
        manager.initialize()

        for i in range(5):
            manager.update_requirement(f"REQ-{i:03d}", f"hash{i}", i+1, None)
            manager.mark_synced()

        assert manager.state.sync_count == 5
        assert len(manager.state.requirements) == 5
