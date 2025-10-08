"""
SysML V2 Requirement Extractor

Extracts requirement definitions and constraints from SysML V2 models via API.
"""

from .models import (
    Requirement,
    RequirementAttribute,
    Constraint,
    ConstraintKind,
    RequirementMetadata
)
from .client import SysMLV2Client
from .extractor import RequirementExtractor

__all__ = [
    "Requirement",
    "RequirementAttribute",
    "Constraint",
    "ConstraintKind",
    "RequirementMetadata",
    "SysMLV2Client",
    "RequirementExtractor",
]
