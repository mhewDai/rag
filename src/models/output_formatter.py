"""Output formatting and validation for extraction results.

This module provides JSON serialization, validation, and formatting utilities
for extraction results to ensure consistent and schema-compliant output.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import asdict
from datetime import datetime

from src.models.feature_models import (
    ExtractionResult,
    FeatureValue,
    FeatureDefinition,
    ValidationRule,
)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")


class OutputFormatter:
    """
    Formatter for extraction results with validation and serialization.
    
    This class handles:
    - JSON serialization with consistent field names
    - Output validation against feature schema
    - Data type conversion and formatting
    - Schema compliance checking
    """
    
    def __init__(self, feature_schema: Optional[Dict[str, FeatureDefinition]] = None):
        """
        Initialize output formatter.
        
        Args:
            feature_schema: Optional feature schema for validation
        """
        self.feature_schema = feature_schema or {}
    
    def format_to_json(
        self,
        extraction_result: ExtractionResult,
        include_metadata: bool = True,
        include_sources: bool = True,
        pretty: bool = False,
    ) -> str:
        """
        Format extraction result to JSON string.
        
        Args:
            extraction_result: Extraction result to format
            include_metadata: Whether to include processing metadata
            include_sources: Whether to include source chunks and pages
            pretty: Whether to pretty-print JSON
            
        Returns:
            JSON string representation
        """
        output_dict = self.to_dict(
            extraction_result,
            include_metadata=include_metadata,
            include_sources=include_sources,
        )
        
        indent = 2 if pretty else None
        return json.dumps(output_dict, indent=indent, ensure_ascii=False)
    
    def to_dict(
        self,
        extraction_result: ExtractionResult,
        include_metadata: bool = True,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert extraction result to dictionary.
        
        Args:
            extraction_result: Extraction result to convert
            include_metadata: Whether to include processing metadata
            include_sources: Whether to include source chunks and pages
            
        Returns:
            Dictionary representation with consistent field names
        """
        output = {
            "document_id": extraction_result.doc_id,
            "features": {},
        }
        
        # Format each feature
        for feature_name, feature_value in extraction_result.features.items():
            formatted_feature = self._format_feature_value(
                feature_value,
                include_sources=include_sources,
            )
            output["features"][feature_name] = formatted_feature
        
        # Add metadata if requested
        if include_metadata:
            output["metadata"] = {
                "processing_time_seconds": round(extraction_result.processing_time, 3),
                "extraction_timestamp": datetime.utcnow().isoformat() + "Z",
                **extraction_result.metadata,
            }
        
        return output
    
    def _format_feature_value(
        self,
        feature_value: FeatureValue,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Format a single feature value.
        
        Args:
            feature_value: Feature value to format
            include_sources: Whether to include source information
            
        Returns:
            Formatted feature dictionary
        """
        formatted = {
            "value": feature_value.value,
            "confidence": round(feature_value.confidence, 3),
        }
        
        if include_sources:
            formatted["sources"] = {
                "pages": feature_value.source_pages,
                "chunk_count": len(feature_value.source_chunks),
            }
        
        return formatted

    
    def validate(
        self,
        extraction_result: ExtractionResult,
        strict: bool = False,
    ) -> List[ValidationError]:
        """
        Validate extraction result against feature schema.
        
        Args:
            extraction_result: Extraction result to validate
            strict: If True, raise exception on first error; if False, collect all errors
            
        Returns:
            List of validation errors (empty if valid)
            
        Raises:
            ValidationError: If strict=True and validation fails
        """
        errors = []
        
        # Check if schema is available
        if not self.feature_schema:
            return errors
        
        # Validate each feature
        for feature_name, feature_def in self.feature_schema.items():
            # Check if feature exists in result
            if feature_name not in extraction_result.features:
                if feature_def.required:
                    error = ValidationError(
                        feature_name,
                        "Required feature is missing from extraction result"
                    )
                    if strict:
                        raise error
                    errors.append(error)
                continue
            
            feature_value = extraction_result.features[feature_name]
            
            # Validate the feature value
            feature_errors = self._validate_feature_value(
                feature_name,
                feature_value,
                feature_def,
            )
            
            if strict and feature_errors:
                raise feature_errors[0]
            
            errors.extend(feature_errors)
        
        return errors
    
    def _validate_feature_value(
        self,
        feature_name: str,
        feature_value: FeatureValue,
        feature_def: FeatureDefinition,
    ) -> List[ValidationError]:
        """
        Validate a single feature value against its definition.
        
        Args:
            feature_name: Name of the feature
            feature_value: Feature value to validate
            feature_def: Feature definition with validation rules
            
        Returns:
            List of validation errors
        """
        errors = []
        value = feature_value.value
        
        # Check required fields
        if feature_def.required and value is None:
            errors.append(ValidationError(
                feature_name,
                "Required feature has null value"
            ))
            return errors
        
        # If value is None and not required, skip further validation
        if value is None:
            return errors
        
        # Apply validation rules
        for rule in feature_def.validation_rules:
            rule_errors = self._apply_validation_rule(
                feature_name,
                value,
                rule,
                feature_def.data_type,
            )
            errors.extend(rule_errors)
        
        return errors
    
    def _apply_validation_rule(
        self,
        feature_name: str,
        value: Any,
        rule: ValidationRule,
        data_type: str,
    ) -> List[ValidationError]:
        """
        Apply a single validation rule.
        
        Args:
            feature_name: Name of the feature
            value: Value to validate
            rule: Validation rule to apply
            data_type: Data type of the feature
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if rule.rule_type == "min_length":
                if len(str(value)) < rule.parameters.get("min", 0):
                    errors.append(ValidationError(
                        feature_name,
                        f"Value length {len(str(value))} is less than minimum {rule.parameters['min']}"
                    ))
            
            elif rule.rule_type == "max_length":
                if len(str(value)) > rule.parameters.get("max", float('inf')):
                    errors.append(ValidationError(
                        feature_name,
                        f"Value length {len(str(value))} exceeds maximum {rule.parameters['max']}"
                    ))
            
            elif rule.rule_type == "pattern":
                pattern = rule.parameters.get("regex", "")
                if not re.search(pattern, str(value), re.IGNORECASE):
                    errors.append(ValidationError(
                        feature_name,
                        f"Value does not match required pattern: {pattern}"
                    ))
            
            elif rule.rule_type == "currency_format":
                # Validate currency format
                if not self._is_valid_currency(value, rule.parameters):
                    errors.append(ValidationError(
                        feature_name,
                        f"Invalid currency format: {value}"
                    ))
            
            elif rule.rule_type == "date_format":
                # Validate date format
                if not self._is_valid_date(value, rule.parameters):
                    errors.append(ValidationError(
                        feature_name,
                        f"Invalid date format: {value}"
                    ))
            
            elif rule.rule_type == "integer":
                # Validate integer
                if not self._is_integer(value):
                    errors.append(ValidationError(
                        feature_name,
                        f"Value is not a valid integer: {value}"
                    ))
            
            elif rule.rule_type == "numeric":
                # Validate numeric (int or float)
                if not self._is_numeric(value):
                    errors.append(ValidationError(
                        feature_name,
                        f"Value is not numeric: {value}"
                    ))
            
            elif rule.rule_type == "range":
                # Validate numeric range
                min_val = rule.parameters.get("min")
                max_val = rule.parameters.get("max")
                numeric_value = self._to_numeric(value)
                
                if numeric_value is not None:
                    if min_val is not None and numeric_value < min_val:
                        errors.append(ValidationError(
                            feature_name,
                            f"Value {numeric_value} is less than minimum {min_val}"
                        ))
                    if max_val is not None and numeric_value > max_val:
                        errors.append(ValidationError(
                            feature_name,
                            f"Value {numeric_value} exceeds maximum {max_val}"
                        ))
            
            elif rule.rule_type == "min_value":
                min_val = rule.parameters.get("min")
                numeric_value = self._to_numeric(value)
                
                if numeric_value is not None and min_val is not None:
                    if numeric_value < min_val:
                        errors.append(ValidationError(
                            feature_name,
                            f"Value {numeric_value} is less than minimum {min_val}"
                        ))
            
            elif rule.rule_type == "enum":
                # Validate enum values
                allowed_values = rule.parameters.get("allowed_values", [])
                case_insensitive = rule.parameters.get("case_insensitive", False)
                
                if case_insensitive:
                    value_lower = str(value).lower()
                    allowed_lower = [str(v).lower() for v in allowed_values]
                    if value_lower not in allowed_lower:
                        errors.append(ValidationError(
                            feature_name,
                            f"Value '{value}' not in allowed values: {allowed_values}"
                        ))
                else:
                    if value not in allowed_values:
                        errors.append(ValidationError(
                            feature_name,
                            f"Value '{value}' not in allowed values: {allowed_values}"
                        ))
        
        except Exception as e:
            errors.append(ValidationError(
                feature_name,
                f"Validation rule '{rule.rule_type}' failed: {str(e)}"
            ))
        
        return errors
    
    def _is_valid_currency(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Check if value is valid currency format."""
        value_str = str(value)
        # Check for currency symbols or numeric value
        currency_pattern = r'^[\$]?\s*[\d,]+\.?\d*$|^\d+\.?\d*\s*(?:USD)?$'
        return bool(re.match(currency_pattern, value_str.strip()))
    
    def _is_valid_date(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Check if value is valid date format."""
        value_str = str(value)
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'[A-Za-z]+\s+\d{1,2},\s+\d{4}',  # Month DD, YYYY
        ]
        return any(re.search(pattern, value_str) for pattern in date_patterns)
    
    def _is_integer(self, value: Any) -> bool:
        """Check if value is an integer."""
        if isinstance(value, int):
            return True
        if isinstance(value, str):
            try:
                int(value.replace(",", ""))
                return True
            except ValueError:
                return False
        return False
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric (int or float)."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(",", ""))
                return True
            except ValueError:
                return False
        return False
    
    def _to_numeric(self, value: Any) -> Optional[float]:
        """Convert value to numeric, return None if not possible."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[\$,]', '', value.strip())
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None
    
    def ensure_schema_compliance(
        self,
        extraction_result: ExtractionResult,
    ) -> ExtractionResult:
        """
        Ensure extraction result complies with schema by adding missing features.
        
        Args:
            extraction_result: Extraction result to check
            
        Returns:
            Updated extraction result with all schema features present
        """
        if not self.feature_schema:
            return extraction_result
        
        # Add missing features with null values
        for feature_name in self.feature_schema.keys():
            if feature_name not in extraction_result.features:
                extraction_result.features[feature_name] = FeatureValue(
                    value=None,
                    confidence=0.0,
                    source_chunks=[],
                    source_pages=[],
                )
        
        return extraction_result
    
    def convert_data_types(
        self,
        extraction_result: ExtractionResult,
    ) -> ExtractionResult:
        """
        Convert feature values to appropriate data types based on schema.
        
        Args:
            extraction_result: Extraction result to convert
            
        Returns:
            Extraction result with converted data types
        """
        if not self.feature_schema:
            return extraction_result
        
        for feature_name, feature_def in self.feature_schema.items():
            if feature_name not in extraction_result.features:
                continue
            
            feature_value = extraction_result.features[feature_name]
            
            if feature_value.value is not None:
                converted_value = self._convert_value(
                    feature_value.value,
                    feature_def.data_type,
                )
                feature_value.value = converted_value
        
        return extraction_result
    
    def _convert_value(self, value: Any, data_type: str) -> Any:
        """
        Convert value to specified data type.
        
        Args:
            value: Value to convert
            data_type: Target data type
            
        Returns:
            Converted value
        """
        if value is None:
            return None
        
        try:
            if data_type == "number":
                # Convert to number (int or float)
                if isinstance(value, str):
                    value = value.replace(",", "")
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            
            elif data_type == "string":
                return str(value)
            
            elif data_type == "currency":
                # Normalize currency format
                return self._normalize_currency(value)
            
            elif data_type == "date":
                # Normalize date format
                return self._normalize_date(value)
            
            else:
                return value
        
        except (ValueError, TypeError):
            # If conversion fails, return original value
            return value
    
    def _normalize_currency(self, value: Any) -> str:
        """Normalize currency value to consistent format."""
        value_str = str(value).strip()
        
        # Extract numeric value
        numeric_match = re.search(r'[\d,]+\.?\d*', value_str)
        if numeric_match:
            numeric_str = numeric_match.group().replace(",", "")
            try:
                amount = float(numeric_str)
                # Format with dollar sign and commas
                return f"${amount:,.2f}"
            except ValueError:
                pass
        
        return value_str
    
    def _normalize_date(self, value: Any) -> str:
        """Normalize date value to consistent format (YYYY-MM-DD)."""
        value_str = str(value).strip()
        
        # Try to parse common date formats
        date_patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        ]
        
        for pattern, formatter in date_patterns:
            match = re.search(pattern, value_str)
            if match:
                return formatter(match)
        
        # If no pattern matches, return as-is
        return value_str


def format_extraction_result(
    extraction_result: ExtractionResult,
    feature_schema: Optional[Dict[str, FeatureDefinition]] = None,
    validate: bool = True,
    ensure_compliance: bool = True,
    convert_types: bool = True,
    include_metadata: bool = True,
    include_sources: bool = True,
    pretty: bool = False,
) -> str:
    """
    Convenience function to format extraction result to JSON.
    
    Args:
        extraction_result: Extraction result to format
        feature_schema: Optional feature schema for validation
        validate: Whether to validate against schema
        ensure_compliance: Whether to ensure all schema features are present
        convert_types: Whether to convert data types
        include_metadata: Whether to include processing metadata
        include_sources: Whether to include source information
        pretty: Whether to pretty-print JSON
        
    Returns:
        JSON string representation
        
    Raises:
        ValidationError: If validation fails and validate=True
    """
    formatter = OutputFormatter(feature_schema)
    
    # Ensure schema compliance
    if ensure_compliance and feature_schema:
        extraction_result = formatter.ensure_schema_compliance(extraction_result)
    
    # Convert data types
    if convert_types and feature_schema:
        extraction_result = formatter.convert_data_types(extraction_result)
    
    # Validate
    if validate and feature_schema:
        errors = formatter.validate(extraction_result, strict=False)
        if errors:
            error_messages = [f"{e.field}: {e.message}" for e in errors]
            raise ValidationError(
                "extraction_result",
                f"Validation failed with {len(errors)} error(s): " + "; ".join(error_messages)
            )
    
    # Format to JSON
    return formatter.format_to_json(
        extraction_result,
        include_metadata=include_metadata,
        include_sources=include_sources,
        pretty=pretty,
    )
