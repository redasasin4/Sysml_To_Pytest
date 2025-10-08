"""
Sync state management

Tracks requirement versions, fingerprints, and sync history
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from datetime import datetime

from .fingerprint import RequirementFingerprint

logger = logging.getLogger(__name__)


@dataclass
class RequirementState:
    """State of a single requirement"""
    requirement_id: str
    content_hash: str
    version: int
    test_file: Optional[Path]
    last_updated: datetime
    has_custom_code: bool = False
    fingerprint: Optional[RequirementFingerprint] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "requirement_id": self.requirement_id,
            "content_hash": self.content_hash,
            "version": self.version,
            "test_file": str(self.test_file) if self.test_file else None,
            "last_updated": self.last_updated.isoformat(),
            "has_custom_code": self.has_custom_code,
            "fingerprint": self.fingerprint.to_dict() if self.fingerprint else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RequirementState":
        """Create from dictionary"""
        return cls(
            requirement_id=data["requirement_id"],
            content_hash=data["content_hash"],
            version=data["version"],
            test_file=Path(data["test_file"]) if data.get("test_file") else None,
            last_updated=datetime.fromisoformat(data["last_updated"]),
            has_custom_code=data.get("has_custom_code", False),
            fingerprint=RequirementFingerprint.from_dict(data["fingerprint"]) if data.get("fingerprint") else None,
        )


@dataclass
class TestFileState:
    """State of a test file"""
    file_path: Path
    requirements: List[str]  # Requirement IDs in this file
    last_generated: datetime
    has_custom_code: bool = False
    backup_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "file_path": str(self.file_path),
            "requirements": self.requirements,
            "last_generated": self.last_generated.isoformat(),
            "has_custom_code": self.has_custom_code,
            "backup_count": self.backup_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TestFileState":
        """Create from dictionary"""
        return cls(
            file_path=Path(data["file_path"]),
            requirements=data["requirements"],
            last_generated=datetime.fromisoformat(data["last_generated"]),
            has_custom_code=data.get("has_custom_code", False),
            backup_count=data.get("backup_count", 0),
        )


@dataclass
class SyncState:
    """Complete sync state"""
    last_sync: Optional[datetime] = None
    requirements: Dict[str, RequirementState] = field(default_factory=dict)
    test_files: Dict[str, TestFileState] = field(default_factory=dict)
    sync_count: int = 0

    def get_requirement(self, requirement_id: str) -> Optional[RequirementState]:
        """Get requirement state by ID"""
        return self.requirements.get(requirement_id)

    def add_requirement(self, req_state: RequirementState):
        """Add or update requirement state"""
        self.requirements[req_state.requirement_id] = req_state

    def remove_requirement(self, requirement_id: str):
        """Remove requirement state"""
        if requirement_id in self.requirements:
            del self.requirements[requirement_id]

    def get_test_file(self, file_path: Path) -> Optional[TestFileState]:
        """Get test file state"""
        return self.test_files.get(str(file_path))

    def add_test_file(self, test_state: TestFileState):
        """Add or update test file state"""
        self.test_files[str(test_state.file_path)] = test_state

    def get_requirements_in_file(self, file_path: Path) -> List[str]:
        """Get all requirement IDs in a test file"""
        test_state = self.get_test_file(file_path)
        return test_state.requirements if test_state else []

    def get_files_for_requirement(self, requirement_id: str) -> List[Path]:
        """Get all test files that contain a requirement"""
        files = []
        for test_state in self.test_files.values():
            if requirement_id in test_state.requirements:
                files.append(test_state.file_path)
        return files

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_count": self.sync_count,
            "requirements": {
                req_id: req_state.to_dict()
                for req_id, req_state in self.requirements.items()
            },
            "test_files": {
                file_path: test_state.to_dict()
                for file_path, test_state in self.test_files.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SyncState":
        """Create from dictionary"""
        return cls(
            last_sync=datetime.fromisoformat(data["last_sync"]) if data.get("last_sync") else None,
            sync_count=data.get("sync_count", 0),
            requirements={
                req_id: RequirementState.from_dict(req_data)
                for req_id, req_data in data.get("requirements", {}).items()
            },
            test_files={
                file_path: TestFileState.from_dict(test_data)
                for file_path, test_data in data.get("test_files", {}).items()
            },
        )


class SyncStateManager:
    """Manages sync state persistence"""

    DEFAULT_STATE_DIR = ".sysml2pytest"
    DEFAULT_STATE_FILE = "sync_state.json"

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize state manager

        Args:
            state_dir: Directory for sync state (default: .sysml2pytest)
        """
        self.state_dir = state_dir or Path.cwd() / self.DEFAULT_STATE_DIR
        self.state_file = self.state_dir / self.DEFAULT_STATE_FILE
        self.state: Optional[SyncState] = None

    def initialize(self):
        """Initialize state directory and file"""
        self.state_dir.mkdir(parents=True, exist_ok=True)

        if not self.state_file.exists():
            logger.info(f"Creating new sync state at {self.state_file}")
            self.state = SyncState()
            self.save()
        else:
            logger.info(f"Loading existing sync state from {self.state_file}")
            self.load()

    def load(self) -> SyncState:
        """Load sync state from file"""
        if not self.state_file.exists():
            logger.warning(f"Sync state file not found: {self.state_file}")
            self.state = SyncState()
            return self.state

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            self.state = SyncState.from_dict(data)
            logger.info(f"Loaded sync state: {len(self.state.requirements)} requirements, "
                       f"{len(self.state.test_files)} test files")
            return self.state

        except Exception as e:
            logger.error(f"Failed to load sync state: {e}")
            self.state = SyncState()
            return self.state

    def save(self):
        """Save sync state to file"""
        if self.state is None:
            logger.warning("No state to save")
            return

        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)

            logger.info(f"Saved sync state to {self.state_file}")

        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")
            raise

    def update_requirement(
        self,
        requirement_id: str,
        content_hash: str,
        version: int,
        test_file: Optional[Path] = None,
        has_custom_code: bool = False,
        fingerprint: Optional[RequirementFingerprint] = None
    ):
        """Update requirement state"""
        if self.state is None:
            self.state = SyncState()

        req_state = RequirementState(
            requirement_id=requirement_id,
            content_hash=content_hash,
            version=version,
            test_file=test_file,
            last_updated=datetime.now(),
            has_custom_code=has_custom_code,
            fingerprint=fingerprint,
        )

        self.state.add_requirement(req_state)

    def update_test_file(
        self,
        file_path: Path,
        requirements: List[str],
        has_custom_code: bool = False
    ):
        """Update test file state"""
        if self.state is None:
            self.state = SyncState()

        test_state = TestFileState(
            file_path=file_path,
            requirements=requirements,
            last_generated=datetime.now(),
            has_custom_code=has_custom_code,
        )

        self.state.add_test_file(test_state)

    def mark_synced(self):
        """Mark that a sync has completed"""
        if self.state is None:
            self.state = SyncState()

        self.state.last_sync = datetime.now()
        self.state.sync_count += 1
        self.save()

    def get_requirement_version(self, requirement_id: str) -> int:
        """Get current version of a requirement"""
        if self.state is None:
            return 0

        req_state = self.state.get_requirement(requirement_id)
        return req_state.version if req_state else 0

    def has_requirement(self, requirement_id: str) -> bool:
        """Check if requirement is tracked"""
        if self.state is None:
            return False

        return requirement_id in self.state.requirements

    def get_all_requirements(self) -> List[RequirementState]:
        """Get all tracked requirements"""
        if self.state is None:
            return []

        return list(self.state.requirements.values())

    def get_stale_requirements(self, current_ids: Set[str]) -> List[str]:
        """Get requirement IDs that are no longer in current set (deleted)"""
        if self.state is None:
            return []

        tracked_ids = set(self.state.requirements.keys())
        return list(tracked_ids - current_ids)

    def cleanup_stale_requirements(self, current_ids: Set[str]):
        """Remove requirements that no longer exist"""
        stale = self.get_stale_requirements(current_ids)
        for req_id in stale:
            logger.info(f"Removing stale requirement: {req_id}")
            self.state.remove_requirement(req_id)

        if stale:
            self.save()

    def print_summary(self):
        """Print summary of sync state"""
        if self.state is None:
            print("No sync state loaded")
            return

        print("=" * 70)
        print("Sync State Summary")
        print("=" * 70)
        print(f"Last sync: {self.state.last_sync.isoformat() if self.state.last_sync else 'Never'}")
        print(f"Sync count: {self.state.sync_count}")
        print(f"Requirements tracked: {len(self.state.requirements)}")
        print(f"Test files tracked: {len(self.state.test_files)}")

        if self.state.requirements:
            print("\nRequirements:")
            for req_id, req_state in sorted(self.state.requirements.items())[:10]:
                print(f"  {req_id}: v{req_state.version}, "
                      f"hash={req_state.content_hash[:8]}..., "
                      f"custom={req_state.has_custom_code}")

            if len(self.state.requirements) > 10:
                print(f"  ... and {len(self.state.requirements) - 10} more")

        print("=" * 70)
