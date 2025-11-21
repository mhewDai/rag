"""Property feature schema definitions for extraction.

This module defines the complete schema for all property features that can be
extracted from property documents, including validation rules and extraction prompts.
"""

from typing import Dict, List
from src.models.feature_models import FeatureDefinition, ValidationRule


def create_property_feature_schema() -> Dict[str, FeatureDefinition]:
    """
    Create the complete schema for all property features.
    
    Returns:
        Dictionary mapping feature names to their definitions
    """
    return {
        "owner_name": FeatureDefinition(
            name="owner_name",
            description="The name of the property owner",
            data_type="string",
            required=True,
            extraction_prompt=(
                "Extract the property owner's name from the document. "
                "Look for sections labeled 'Owner', 'Property Owner', or similar. "
                "Return the full name as it appears in the document."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="min_length",
                    parameters={"min": 2}
                ),
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 200}
                )
            ]
        ),
        
        "property_address": FeatureDefinition(
            name="property_address",
            description="The full address of the property",
            data_type="string",
            required=True,
            extraction_prompt=(
                "Extract the complete property address including street number, "
                "street name, city, state, and ZIP code. Look for sections labeled "
                "'Property Address', 'Location', or 'Site Address'."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="min_length",
                    parameters={"min": 10}
                ),
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 300}
                )
            ]
        ),
        
        "lot_size": FeatureDefinition(
            name="lot_size",
            description="The size of the lot in acres or square feet",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the lot size from the document. Look for sections labeled "
                "'Lot Size', 'Land Area', or 'Acreage'. Include the unit of measurement "
                "(acres, square feet, etc.) in the extracted value."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="pattern",
                    parameters={"regex": r"[\d.,]+\s*(acres?|sq\.?\s*ft\.?|square feet)"}
                )
            ]
        ),
        
        "sale_price": FeatureDefinition(
            name="sale_price",
            description="The most recent sale price of the property",
            data_type="currency",
            required=False,
            extraction_prompt=(
                "Extract the most recent sale price from the document. "
                "Look for sections labeled 'Sale Price', 'Purchase Price', or "
                "'Consideration'. Return the amount with currency symbol if present."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="currency_format",
                    parameters={"allow_symbols": ["$", "USD"]}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "sale_date": FeatureDefinition(
            name="sale_date",
            description="The date of the most recent sale",
            data_type="date",
            required=False,
            extraction_prompt=(
                "Extract the date of the most recent property sale. "
                "Look for sections labeled 'Sale Date', 'Date of Sale', or "
                "'Transfer Date'. Return in a standard date format."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="date_format",
                    parameters={"formats": ["MM/DD/YYYY", "YYYY-MM-DD", "Month DD, YYYY"]}
                )
            ]
        ),
        
        "property_type": FeatureDefinition(
            name="property_type",
            description="The type or classification of the property",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the property type from the document. "
                "Look for sections labeled 'Property Type', 'Classification', or "
                "'Use Code'. Common values include: Residential, Commercial, "
                "Industrial, Agricultural, Vacant Land, Multi-Family, etc."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="enum",
                    parameters={
                        "allowed_values": [
                            "Residential", "Commercial", "Industrial", 
                            "Agricultural", "Vacant Land", "Multi-Family",
                            "Mixed Use", "Other"
                        ],
                        "case_insensitive": True
                    }
                )
            ]
        ),
        
        "bedrooms": FeatureDefinition(
            name="bedrooms",
            description="The number of bedrooms in the property",
            data_type="number",
            required=False,
            extraction_prompt=(
                "Extract the number of bedrooms from the document. "
                "Look for sections labeled 'Bedrooms', 'BR', 'Beds', or "
                "building description sections. Return only the numeric value."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="integer",
                    parameters={}
                ),
                ValidationRule(
                    rule_type="range",
                    parameters={"min": 0, "max": 50}
                )
            ]
        ),
        
        "bathrooms": FeatureDefinition(
            name="bathrooms",
            description="The number of bathrooms in the property",
            data_type="number",
            required=False,
            extraction_prompt=(
                "Extract the number of bathrooms from the document. "
                "Look for sections labeled 'Bathrooms', 'BA', 'Baths', or "
                "building description sections. Include half baths (e.g., 2.5)."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="numeric",
                    parameters={"allow_decimal": True}
                ),
                ValidationRule(
                    rule_type="range",
                    parameters={"min": 0, "max": 50}
                )
            ]
        ),
        
        "year_built": FeatureDefinition(
            name="year_built",
            description="The year the property was built",
            data_type="number",
            required=False,
            extraction_prompt=(
                "Extract the year the property was built from the document. "
                "Look for sections labeled 'Year Built', 'Construction Date', or "
                "'Built'. Return only the 4-digit year."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="integer",
                    parameters={}
                ),
                ValidationRule(
                    rule_type="range",
                    parameters={"min": 1600, "max": 2100}
                )
            ]
        ),
        
        "square_footage": FeatureDefinition(
            name="square_footage",
            description="The total square footage of the building",
            data_type="number",
            required=False,
            extraction_prompt=(
                "Extract the total square footage of the building from the document. "
                "Look for sections labeled 'Square Footage', 'Building Area', "
                "'Living Area', or 'Total SF'. Return only the numeric value."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="integer",
                    parameters={}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "tax_assessment_value": FeatureDefinition(
            name="tax_assessment_value",
            description="The assessed value for tax purposes",
            data_type="currency",
            required=False,
            extraction_prompt=(
                "Extract the tax assessment value from the document. "
                "Look for sections labeled 'Assessed Value', 'Tax Assessment', "
                "'Assessment', or 'Taxable Value'. Return the amount with currency symbol."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="currency_format",
                    parameters={"allow_symbols": ["$", "USD"]}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "annual_property_tax": FeatureDefinition(
            name="annual_property_tax",
            description="The annual property tax amount",
            data_type="currency",
            required=False,
            extraction_prompt=(
                "Extract the annual property tax amount from the document. "
                "Look for sections labeled 'Annual Tax', 'Property Tax', "
                "'Yearly Tax', or 'Tax Amount'. Return the amount with currency symbol."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="currency_format",
                    parameters={"allow_symbols": ["$", "USD"]}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "zoning_classification": FeatureDefinition(
            name="zoning_classification",
            description="The zoning classification or code",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the zoning classification from the document. "
                "Look for sections labeled 'Zoning', 'Zone', 'Zoning Code', or "
                "'Land Use'. Return the exact code or classification as it appears."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 50}
                )
            ]
        ),
        
        "parcel_id": FeatureDefinition(
            name="parcel_id",
            description="The unique parcel identification number",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the parcel ID or identification number from the document. "
                "Look for sections labeled 'Parcel ID', 'Parcel Number', 'Tax ID', "
                "'Property ID', or 'Account Number'. Return the exact identifier."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 100}
                )
            ]
        ),
        
        "legal_description": FeatureDefinition(
            name="legal_description",
            description="The legal description of the property",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the legal description of the property from the document. "
                "Look for sections labeled 'Legal Description', 'Legal', or "
                "'Property Description'. This typically includes lot, block, and "
                "subdivision information."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 1000}
                )
            ]
        ),
        
        "previous_sale_price": FeatureDefinition(
            name="previous_sale_price",
            description="The previous sale price before the most recent sale",
            data_type="currency",
            required=False,
            extraction_prompt=(
                "Extract the previous sale price from the document. "
                "Look for sections showing sale history or prior sales. "
                "Return the sale price that occurred before the most recent sale."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="currency_format",
                    parameters={"allow_symbols": ["$", "USD"]}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "previous_sale_date": FeatureDefinition(
            name="previous_sale_date",
            description="The date of the previous sale",
            data_type="date",
            required=False,
            extraction_prompt=(
                "Extract the date of the previous property sale from the document. "
                "Look for sections showing sale history. Return the date that "
                "occurred before the most recent sale."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="date_format",
                    parameters={"formats": ["MM/DD/YYYY", "YYYY-MM-DD", "Month DD, YYYY"]}
                )
            ]
        ),
        
        "mortgage_amount": FeatureDefinition(
            name="mortgage_amount",
            description="The mortgage or loan amount",
            data_type="currency",
            required=False,
            extraction_prompt=(
                "Extract the mortgage or loan amount from the document. "
                "Look for sections labeled 'Mortgage', 'Loan Amount', "
                "'Financing', or 'Lien Amount'. Return the amount with currency symbol."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="currency_format",
                    parameters={"allow_symbols": ["$", "USD"]}
                ),
                ValidationRule(
                    rule_type="min_value",
                    parameters={"min": 0}
                )
            ]
        ),
        
        "deed_book_reference": FeatureDefinition(
            name="deed_book_reference",
            description="The deed book reference number",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the deed book reference from the document. "
                "Look for sections labeled 'Deed Book', 'Book', 'Deed Reference', "
                "or 'Recording Information'. This is typically a book number."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 50}
                )
            ]
        ),
        
        "page_number": FeatureDefinition(
            name="page_number",
            description="The page number in the deed book",
            data_type="string",
            required=False,
            extraction_prompt=(
                "Extract the page number from the deed book reference. "
                "Look for sections labeled 'Page', 'Pg', or appearing after "
                "the deed book number. This is the page where the deed is recorded."
            ),
            validation_rules=[
                ValidationRule(
                    rule_type="max_length",
                    parameters={"max": 20}
                )
            ]
        ),
    }


def get_feature_names() -> List[str]:
    """
    Get a list of all property feature names.
    
    Returns:
        List of feature names
    """
    return list(create_property_feature_schema().keys())


def get_feature_definition(feature_name: str) -> FeatureDefinition:
    """
    Get the definition for a specific feature.
    
    Args:
        feature_name: Name of the feature
        
    Returns:
        FeatureDefinition for the specified feature
        
    Raises:
        KeyError: If feature name is not found
    """
    schema = create_property_feature_schema()
    if feature_name not in schema:
        raise KeyError(f"Feature '{feature_name}' not found in schema")
    return schema[feature_name]


def get_required_features() -> List[str]:
    """
    Get a list of required property feature names.
    
    Returns:
        List of required feature names
    """
    schema = create_property_feature_schema()
    return [name for name, definition in schema.items() if definition.required]


def get_optional_features() -> List[str]:
    """
    Get a list of optional property feature names.
    
    Returns:
        List of optional feature names
    """
    schema = create_property_feature_schema()
    return [name for name, definition in schema.items() if not definition.required]


# Export the schema for easy access
PROPERTY_FEATURE_SCHEMA = create_property_feature_schema()
