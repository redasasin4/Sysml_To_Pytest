"""
Custom pytest markers for requirements traceability
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RequirementMarker:
    """
    Data extracted from @pytest.mark.requirement marker

    Example usage:
        @pytest.mark.requirement(id="REQ-001", name="TreeHeightRequirement")
        def test_tree_height():
            pass
    """
    id: str
    name: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    stakeholder: Optional[str] = None

    def __str__(self) -> str:
        return f"Requirement({self.id}: {self.name or 'unnamed'})"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "stakeholder": self.stakeholder,
        }

    @classmethod
    def from_marker(cls, marker) -> "RequirementMarker":
        """
        Extract RequirementMarker from pytest marker

        Args:
            marker: pytest.Mark object

        Returns:
            RequirementMarker instance
        """
        kwargs = marker.kwargs
        return cls(
            id=kwargs.get("id", "UNKNOWN"),
            name=kwargs.get("name"),
            category=kwargs.get("category"),
            priority=kwargs.get("priority"),
            stakeholder=kwargs.get("stakeholder"),
        )
