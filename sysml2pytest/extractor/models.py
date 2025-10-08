"""
Data models for SysML V2 requirements
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class ConstraintKind(str, Enum):
    """Type of constraint in a requirement"""
    ASSUME = "assume"  # Precondition
    REQUIRE = "require"  # Postcondition


class AttributeType(str, Enum):
    """Attribute data types"""
    INTEGER = "Integer"
    REAL = "Real"
    BOOLEAN = "Boolean"
    STRING = "String"
    UNKNOWN = "Unknown"


@dataclass
class RequirementAttribute:
    """Represents an attribute within a requirement"""
    name: str
    type: AttributeType
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "default_value": self.default_value,
        }


@dataclass
class Constraint:
    """Represents a constraint expression"""
    kind: ConstraintKind
    expression: str
    raw_expression: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind.value,
            "expression": self.expression,
            "raw_expression": self.raw_expression,
            "description": self.description,
        }


@dataclass
class RequirementMetadata:
    """Metadata about a requirement"""
    id: str
    name: str
    qualified_name: str
    documentation: Optional[str] = None
    stakeholders: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    subject: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "documentation": self.documentation,
            "stakeholders": self.stakeholders,
            "actors": self.actors,
            "subject": self.subject,
            "source_file": self.source_file,
            "line_number": self.line_number,
        }


@dataclass
class Requirement:
    """Complete requirement definition from SysML V2"""
    metadata: RequirementMetadata
    attributes: List[RequirementAttribute] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    nested_requirements: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None

    @property
    def assume_constraints(self) -> List[Constraint]:
        """Get all assume (precondition) constraints"""
        return [c for c in self.constraints if c.kind == ConstraintKind.ASSUME]

    @property
    def require_constraints(self) -> List[Constraint]:
        """Get all require (postcondition) constraints"""
        return [c for c in self.constraints if c.kind == ConstraintKind.REQUIRE]

    def get_attribute(self, name: str) -> Optional[RequirementAttribute]:
        """Get attribute by name"""
        for attr in self.attributes:
            if attr.name == name:
                return attr
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "metadata": self.metadata.to_dict(),
            "attributes": [attr.to_dict() for attr in self.attributes],
            "constraints": [c.to_dict() for c in self.constraints],
            "nested_requirements": self.nested_requirements,
            "raw_data": self.raw_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """Create Requirement from dictionary"""
        metadata = RequirementMetadata(**data["metadata"])
        attributes = [
            RequirementAttribute(
                name=a["name"],
                type=AttributeType(a["type"]),
                description=a.get("description"),
                min_value=a.get("min_value"),
                max_value=a.get("max_value"),
                default_value=a.get("default_value"),
            )
            for a in data.get("attributes", [])
        ]
        constraints = [
            Constraint(
                kind=ConstraintKind(c["kind"]),
                expression=c["expression"],
                raw_expression=c.get("raw_expression"),
                description=c.get("description"),
            )
            for c in data.get("constraints", [])
        ]

        return cls(
            metadata=metadata,
            attributes=attributes,
            constraints=constraints,
            nested_requirements=data.get("nested_requirements", []),
            raw_data=data.get("raw_data"),
        )
