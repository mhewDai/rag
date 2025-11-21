"""Data models for feature extraction."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationRule:
    """A validation rule for a feature."""

    rule_type: str
    parameters: Dict[str, Any]


@dataclass
class FeatureDefinition:
    """Definition of a property feature to extract."""

    name: str
    description: str
    data_type: str  # string, number, date, currency
    required: bool
    extraction_prompt: str
    validation_rules: List[ValidationRule]


@dataclass
class FeatureValue:
    """An extracted feature value with metadata."""

    value: Any
    confidence: float
    source_chunks: List[str]
    source_pages: List[int]


@dataclass
class ExtractionResult:
    """Result of feature extraction from a document."""

    doc_id: str
    features: Dict[str, FeatureValue]
    processing_time: float
    metadata: Dict[str, Any]
