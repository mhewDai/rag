#!/usr/bin/env python3
"""Verification script for output formatting and validation."""

import json
from src.models.feature_models import (
    FeatureDefinition,
    FeatureValue,
    ExtractionResult,
    ValidationRule,
)
from src.models.output_formatter import (
    OutputFormatter,
    ValidationError,
    format_extraction_result,
)


def test_basic_formatting():
    """Test basic JSON formatting."""
    print("Testing basic JSON formatting...")
    
    # Create sample extraction result
    result = ExtractionResult(
        doc_id="test_doc_001",
        features={
            "owner_name": FeatureValue(
                value="John Doe",
                confidence=0.95,
                source_chunks=["Owner: John Doe"],
                source_pages=[1],
            ),
            "sale_price": FeatureValue(
                value="$500,000",
                confidence=0.88,
                source_chunks=["Sale Price: $500,000"],
                source_pages=[2],
            ),
            "bedrooms": FeatureValue(
                value=3,
                confidence=0.92,
                source_chunks=["3 bedrooms"],
                source_pages=[1],
            ),
        },
        processing_time=2.5,
        metadata={"model": "gpt-4", "temperature": 0.1},
    )
    
    formatter = OutputFormatter()
    
    # Test JSON formatting
    json_output = formatter.format_to_json(result, pretty=True)
    print("JSON Output:")
    print(json_output)
    
    # Verify it's valid JSON
    parsed = json.loads(json_output)
    assert parsed["document_id"] == "test_doc_001"
    assert "features" in parsed
    assert "owner_name" in parsed["features"]
    assert parsed["features"]["owner_name"]["value"] == "John Doe"
    assert parsed["features"]["owner_name"]["confidence"] == 0.95
    
    print("✓ Basic formatting test passed\n")


def test_validation():
    """Test validation against schema."""
    print("Testing validation...")
    
    # Create feature schema
    schema = {
        "owner_name": FeatureDefinition(
            name="owner_name",
            description="Property owner name",
            data_type="string",
            required=True,
            extraction_prompt="Extract owner name",
            validation_rules=[
                ValidationRule(rule_type="min_length", parameters={"min": 2}),
                ValidationRule(rule_type="max_length", parameters={"max": 200}),
            ],
        ),
        "bedrooms": FeatureDefinition(
            name="bedrooms",
            description="Number of bedrooms",
            data_type="number",
            required=False,
            extraction_prompt="Extract bedroom count",
            validation_rules=[
                ValidationRule(rule_type="integer", parameters={}),
                ValidationRule(rule_type="range", parameters={"min": 0, "max": 50}),
            ],
        ),
    }
    
    # Test valid result
    valid_result = ExtractionResult(
        doc_id="test_doc_002",
        features={
            "owner_name": FeatureValue(
                value="Jane Smith",
                confidence=0.95,
                source_chunks=["Owner: Jane Smith"],
                source_pages=[1],
            ),
            "bedrooms": FeatureValue(
                value=4,
                confidence=0.90,
                source_chunks=["4 bedrooms"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    formatter = OutputFormatter(schema)
    errors = formatter.validate(valid_result)
    assert len(errors) == 0, f"Expected no errors, got {len(errors)}"
    print("✓ Valid result passed validation")
    
    # Test invalid result (missing required field)
    invalid_result = ExtractionResult(
        doc_id="test_doc_003",
        features={
            "bedrooms": FeatureValue(
                value=4,
                confidence=0.90,
                source_chunks=["4 bedrooms"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    errors = formatter.validate(invalid_result)
    assert len(errors) > 0, "Expected validation errors for missing required field"
    print(f"✓ Invalid result correctly failed validation with {len(errors)} error(s)")
    
    # Test invalid value (out of range)
    invalid_range_result = ExtractionResult(
        doc_id="test_doc_004",
        features={
            "owner_name": FeatureValue(
                value="Bob Johnson",
                confidence=0.95,
                source_chunks=["Owner: Bob Johnson"],
                source_pages=[1],
            ),
            "bedrooms": FeatureValue(
                value=100,  # Out of range
                confidence=0.90,
                source_chunks=["100 bedrooms"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    errors = formatter.validate(invalid_range_result)
    assert len(errors) > 0, "Expected validation errors for out-of-range value"
    print(f"✓ Out-of-range value correctly failed validation\n")


def test_data_type_conversion():
    """Test data type conversion."""
    print("Testing data type conversion...")
    
    schema = {
        "sale_price": FeatureDefinition(
            name="sale_price",
            description="Sale price",
            data_type="currency",
            required=False,
            extraction_prompt="Extract sale price",
            validation_rules=[],
        ),
        "bedrooms": FeatureDefinition(
            name="bedrooms",
            description="Number of bedrooms",
            data_type="number",
            required=False,
            extraction_prompt="Extract bedroom count",
            validation_rules=[],
        ),
        "sale_date": FeatureDefinition(
            name="sale_date",
            description="Sale date",
            data_type="date",
            required=False,
            extraction_prompt="Extract sale date",
            validation_rules=[],
        ),
    }
    
    result = ExtractionResult(
        doc_id="test_doc_005",
        features={
            "sale_price": FeatureValue(
                value="500000",  # No formatting
                confidence=0.88,
                source_chunks=["Price: 500000"],
                source_pages=[1],
            ),
            "bedrooms": FeatureValue(
                value="3",  # String instead of number
                confidence=0.92,
                source_chunks=["3 bedrooms"],
                source_pages=[1],
            ),
            "sale_date": FeatureValue(
                value="01/15/2023",  # MM/DD/YYYY format
                confidence=0.85,
                source_chunks=["Date: 01/15/2023"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    formatter = OutputFormatter(schema)
    converted_result = formatter.convert_data_types(result)
    
    # Check conversions
    assert converted_result.features["sale_price"].value == "$500,000.00"
    print(f"✓ Currency converted: {converted_result.features['sale_price'].value}")
    
    assert converted_result.features["bedrooms"].value == 3
    print(f"✓ Number converted: {converted_result.features['bedrooms'].value}")
    
    assert converted_result.features["sale_date"].value == "2023-01-15"
    print(f"✓ Date converted: {converted_result.features['sale_date'].value}\n")


def test_schema_compliance():
    """Test ensuring schema compliance."""
    print("Testing schema compliance...")
    
    schema = {
        "owner_name": FeatureDefinition(
            name="owner_name",
            description="Property owner name",
            data_type="string",
            required=True,
            extraction_prompt="Extract owner name",
            validation_rules=[],
        ),
        "bedrooms": FeatureDefinition(
            name="bedrooms",
            description="Number of bedrooms",
            data_type="number",
            required=False,
            extraction_prompt="Extract bedroom count",
            validation_rules=[],
        ),
        "bathrooms": FeatureDefinition(
            name="bathrooms",
            description="Number of bathrooms",
            data_type="number",
            required=False,
            extraction_prompt="Extract bathroom count",
            validation_rules=[],
        ),
    }
    
    # Result missing some features
    result = ExtractionResult(
        doc_id="test_doc_006",
        features={
            "owner_name": FeatureValue(
                value="Alice Brown",
                confidence=0.95,
                source_chunks=["Owner: Alice Brown"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    formatter = OutputFormatter(schema)
    compliant_result = formatter.ensure_schema_compliance(result)
    
    # Check that all schema features are present
    assert "owner_name" in compliant_result.features
    assert "bedrooms" in compliant_result.features
    assert "bathrooms" in compliant_result.features
    
    # Check that missing features have null values
    assert compliant_result.features["bedrooms"].value is None
    assert compliant_result.features["bathrooms"].value is None
    
    print(f"✓ Schema compliance ensured: {len(compliant_result.features)} features present\n")


def test_convenience_function():
    """Test the convenience function."""
    print("Testing convenience function...")
    
    schema = {
        "owner_name": FeatureDefinition(
            name="owner_name",
            description="Property owner name",
            data_type="string",
            required=True,
            extraction_prompt="Extract owner name",
            validation_rules=[],
        ),
    }
    
    result = ExtractionResult(
        doc_id="test_doc_007",
        features={
            "owner_name": FeatureValue(
                value="Charlie Davis",
                confidence=0.95,
                source_chunks=["Owner: Charlie Davis"],
                source_pages=[1],
            ),
        },
        processing_time=1.5,
        metadata={},
    )
    
    # Use convenience function
    json_output = format_extraction_result(
        result,
        feature_schema=schema,
        validate=True,
        ensure_compliance=True,
        convert_types=True,
        pretty=True,
    )
    
    parsed = json.loads(json_output)
    assert parsed["document_id"] == "test_doc_007"
    assert parsed["features"]["owner_name"]["value"] == "Charlie Davis"
    
    print("✓ Convenience function works correctly\n")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Output Formatter Verification")
    print("=" * 60 + "\n")
    
    try:
        test_basic_formatting()
        test_validation()
        test_data_type_conversion()
        test_schema_compliance()
        test_convenience_function()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
