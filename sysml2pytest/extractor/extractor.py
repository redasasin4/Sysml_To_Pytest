"""
SysML V2 Requirement Extractor

Extracts and parses requirement definitions from SysML V2 models
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .client import SysMLV2Client
from .models import (
    Requirement,
    RequirementAttribute,
    RequirementMetadata,
    Constraint,
    ConstraintKind,
    AttributeType,
)

logger = logging.getLogger(__name__)


class RequirementExtractor:
    """Extracts requirements from SysML V2 models"""

    def __init__(self, client: SysMLV2Client):
        """
        Initialize extractor

        Args:
            client: SysML V2 API client
        """
        self.client = client

    def extract_requirements(
        self,
        project_id: str,
        commit_id: Optional[str] = None,
        include_usages: bool = False
    ) -> List[Requirement]:
        """
        Extract all requirements from a project

        Args:
            project_id: SysML V2 project identifier
            commit_id: Specific commit (optional, uses HEAD)
            include_usages: Whether to include requirement usages

        Returns:
            List of extracted requirements
        """
        logger.info(f"Extracting requirements from project {project_id}")

        # Get requirement definitions
        req_defs = self.client.get_requirement_definitions(project_id, commit_id)
        logger.info(f"Found {len(req_defs)} requirement definitions")

        requirements = []
        for req_def in req_defs:
            try:
                req = self._parse_requirement_definition(req_def, project_id, commit_id)
                requirements.append(req)
            except Exception as e:
                logger.error(f"Failed to parse requirement {req_def.get('name', 'unknown')}: {e}")

        # Optionally get requirement usages
        if include_usages:
            req_usages = self.client.get_requirement_usages(project_id, commit_id)
            logger.info(f"Found {len(req_usages)} requirement usages")
            # Process usages similarly...

        logger.info(f"Successfully extracted {len(requirements)} requirements")
        return requirements

    def _parse_requirement_definition(
        self,
        req_data: Dict[str, Any],
        project_id: str,
        commit_id: Optional[str] = None
    ) -> Requirement:
        """
        Parse a requirement definition element into Requirement object

        Args:
            req_data: Raw requirement definition data from API
            project_id: Project ID
            commit_id: Commit ID

        Returns:
            Parsed Requirement object
        """
        # Extract metadata
        metadata = self._extract_metadata(req_data)

        # Extract attributes
        attributes = self._extract_attributes(req_data, project_id, commit_id)

        # Extract constraints
        constraints = self._extract_constraints(req_data, project_id, commit_id)

        # Extract nested requirements
        nested_reqs = self._extract_nested_requirements(req_data, project_id, commit_id)

        return Requirement(
            metadata=metadata,
            attributes=attributes,
            constraints=constraints,
            nested_requirements=nested_reqs,
            raw_data=req_data
        )

    def _extract_metadata(self, req_data: Dict[str, Any]) -> RequirementMetadata:
        """Extract requirement metadata"""
        return RequirementMetadata(
            id=req_data.get("@id", ""),
            name=req_data.get("name", "UnnamedRequirement"),
            qualified_name=req_data.get("qualifiedName", ""),
            documentation=req_data.get("documentation", req_data.get("doc", "")),
            stakeholders=self._extract_stakeholders(req_data),
            actors=self._extract_actors(req_data),
            subject=self._extract_subject(req_data),
            source_file=req_data.get("sourceFile"),
            line_number=req_data.get("lineNumber"),
        )

    def _extract_attributes(
        self,
        req_data: Dict[str, Any],
        project_id: str,
        commit_id: Optional[str] = None
    ) -> List[RequirementAttribute]:
        """Extract attributes from requirement definition"""
        attributes = []

        # Look for owned attributes/features
        for feature in req_data.get("ownedFeature", []):
            if self._is_attribute(feature):
                attr = self._parse_attribute(feature)
                if attr:
                    attributes.append(attr)

        return attributes

    def _extract_constraints(
        self,
        req_data: Dict[str, Any],
        project_id: str,
        commit_id: Optional[str] = None
    ) -> List[Constraint]:
        """Extract constraints from requirement definition"""
        constraints = []

        # Look for constraint usages
        for feature in req_data.get("ownedFeature", []):
            if self._is_constraint(feature):
                constraint = self._parse_constraint(feature)
                if constraint:
                    constraints.append(constraint)

        return constraints

    def _extract_nested_requirements(
        self,
        req_data: Dict[str, Any],
        project_id: str,
        commit_id: Optional[str] = None
    ) -> List[str]:
        """Extract nested/referenced requirements"""
        nested = []

        # Look for requirement usages within this requirement
        for feature in req_data.get("ownedFeature", []):
            if feature.get("@type") == "RequirementUsage":
                nested.append(feature.get("name", feature.get("@id", "")))

        return nested

    def _extract_stakeholders(self, req_data: Dict[str, Any]) -> List[str]:
        """Extract stakeholder references"""
        # Look for stakeholder features
        return [
            f.get("name", "")
            for f in req_data.get("ownedFeature", [])
            if f.get("declaredName") == "stakeholder"
        ]

    def _extract_actors(self, req_data: Dict[str, Any]) -> List[str]:
        """Extract actor references"""
        return [
            f.get("name", "")
            for f in req_data.get("ownedFeature", [])
            if f.get("declaredName") == "actor"
        ]

    def _extract_subject(self, req_data: Dict[str, Any]) -> Optional[str]:
        """Extract subject parameter"""
        for feature in req_data.get("ownedFeature", []):
            if feature.get("declaredName") == "subject":
                return feature.get("name", "")
        return None

    def _is_attribute(self, feature: Dict[str, Any]) -> bool:
        """Check if feature is an attribute"""
        return feature.get("@type") in ["AttributeUsage", "AttributeDefinition"]

    def _is_constraint(self, feature: Dict[str, Any]) -> bool:
        """Check if feature is a constraint"""
        return feature.get("@type") in ["ConstraintUsage", "RequireConstraintUsage", "AssumeConstraintUsage"]

    def _parse_attribute(self, feature: Dict[str, Any]) -> Optional[RequirementAttribute]:
        """Parse attribute feature into RequirementAttribute"""
        name = feature.get("name", feature.get("declaredName", ""))
        if not name:
            return None

        # Determine type
        type_str = feature.get("type", {}).get("name", "Unknown")
        attr_type = self._map_type(type_str)

        return RequirementAttribute(
            name=name,
            type=attr_type,
            description=feature.get("documentation"),
        )

    def _parse_constraint(self, feature: Dict[str, Any]) -> Optional[Constraint]:
        """Parse constraint feature into Constraint"""
        # Determine constraint kind
        feature_type = feature.get("@type", "")
        if "Assume" in feature_type or "assume" in feature.get("name", "").lower():
            kind = ConstraintKind.ASSUME
        else:
            kind = ConstraintKind.REQUIRE

        # Extract expression
        expression = self._extract_expression(feature)
        if not expression:
            return None

        return Constraint(
            kind=kind,
            expression=expression,
            raw_expression=feature.get("body", {}).get("expression"),
            description=feature.get("documentation"),
        )

    def _extract_expression(self, constraint_feature: Dict[str, Any]) -> Optional[str]:
        """Extract constraint expression string"""
        # Try to get expression body
        body = constraint_feature.get("body", {})
        if isinstance(body, dict):
            return body.get("expression", body.get("result", {}).get("expression"))
        elif isinstance(body, str):
            return body
        return None

    def _map_type(self, type_str: str) -> AttributeType:
        """Map SysML type name to AttributeType enum"""
        type_mapping = {
            "Integer": AttributeType.INTEGER,
            "Real": AttributeType.REAL,
            "Boolean": AttributeType.BOOLEAN,
            "String": AttributeType.STRING,
        }
        return type_mapping.get(type_str, AttributeType.UNKNOWN)

    def save_requirements(self, requirements: List[Requirement], output_file: Path) -> None:
        """
        Save requirements to JSON file

        Args:
            requirements: List of requirements
            output_file: Output file path
        """
        data = {
            "requirements": [req.to_dict() for req in requirements],
            "count": len(requirements),
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(requirements)} requirements to {output_file}")

    @staticmethod
    def load_requirements(input_file: Path) -> List[Requirement]:
        """
        Load requirements from JSON file

        Args:
            input_file: Input file path

        Returns:
            List of requirements
        """
        with open(input_file, "r") as f:
            data = json.load(f)

        requirements = [
            Requirement.from_dict(req_data)
            for req_data in data.get("requirements", [])
        ]

        logger.info(f"Loaded {len(requirements)} requirements from {input_file}")
        return requirements
