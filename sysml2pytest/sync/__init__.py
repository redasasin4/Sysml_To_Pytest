"""
Sync module for keeping requirements and tests synchronized
"""

from .fingerprint import RequirementFingerprint, compute_requirement_hash
from .detector import SyncDetector, SyncReport, RequirementChange, ChangeType
from .state import SyncState, SyncStateManager, RequirementState, TestFileState
from .parser import TestFileParser, ParsedTest, TestMetadata, ProtectedRegion
from .updater import TestUpdater, UpdateStrategy, UpdateResult

__all__ = [
    "RequirementFingerprint",
    "compute_requirement_hash",
    "SyncDetector",
    "SyncReport",
    "RequirementChange",
    "ChangeType",
    "SyncState",
    "SyncStateManager",
    "RequirementState",
    "TestFileState",
    "TestFileParser",
    "ParsedTest",
    "TestMetadata",
    "ProtectedRegion",
    "TestUpdater",
    "UpdateStrategy",
    "UpdateResult",
]
