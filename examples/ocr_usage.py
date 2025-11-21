"""Example usage of the OCR module."""

from pathlib import Path
from src.ocr import OCRModule, InvalidPDFError, OCRProcessingError
from src.config.settings import OCRConfig


def basic_ocr_example():
    """Basic example of using the OCR module."""
    print("Basic OCR Example")
    print("-" * 50)
    
    # Create OCR configuration
    config = OCRConfig(
        language="eng",
        dpi=300,
        preprocess=True,
        denoise=True,
        deskew=True,
        contrast_enhancement=True
    )
    
    # Initialize OCR module
    ocr = OCRModule(config)
    
    # Extract text from PDF
    pdf_path = "monmouth_property.pdf"
    
    try:
        result = ocr.extract_text(pdf_path)
        
        print(f"Successfully extracted text from {pdf_path}")
        print(f"Number of pages: {len(result.pages)}")
        print(f"Overall confidence: {result.confidence:.2%}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"\nFirst 500 characters:\n{result.text[:500]}")
        
    except InvalidPDFError as e:
        print(f"Invalid PDF: {e}")
    except OCRProcessingError as e:
        print(f"OCR processing failed: {e}")


def custom_config_example():
    """Example with custom OCR configuration."""
    print("\n\nCustom Configuration Example")
    print("-" * 50)
    
    # Create custom configuration for high-quality scans
    config = OCRConfig(
        language="eng",
        dpi=600,  # Higher DPI for better quality
        preprocess=True,
        denoise=False,  # Disable if scan is already clean
        deskew=True,
        contrast_enhancement=False
    )
    
    ocr = OCRModule(config)
    print(f"OCR configured with DPI: {config.dpi}")
    print(f"Preprocessing: {config.preprocess}")
    print(f"Denoising: {config.denoise}")


def page_by_page_example():
    """Example showing page-by-page processing."""
    print("\n\nPage-by-Page Processing Example")
    print("-" * 50)
    
    config = OCRConfig()
    ocr = OCRModule(config)
    
    pdf_path = "monmouth_property.pdf"
    
    if not Path(pdf_path).exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    try:
        result = ocr.extract_text(pdf_path)
        
        print(f"Processing {len(result.pages)} pages:\n")
        
        for page in result.pages:
            print(f"Page {page.page_number}:")
            print(f"  Text length: {len(page.text)} characters")
            print(f"  Confidence: {page.confidence:.2%}")
            print(f"  Dimensions: {page.width}x{page.height}")
            print(f"  Preview: {page.text[:100].replace(chr(10), ' ')}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")


def error_handling_example():
    """Example showing error handling."""
    print("\n\nError Handling Example")
    print("-" * 50)
    
    config = OCRConfig()
    ocr = OCRModule(config)
    
    # Test various error conditions
    test_cases = [
        ("nonexistent.pdf", "Non-existent file"),
        (".", "Directory instead of file"),
        ("README.md", "Non-PDF file"),
    ]
    
    for pdf_path, description in test_cases:
        print(f"\nTesting: {description}")
        try:
            result = ocr.extract_text(pdf_path)
            print(f"  Unexpected success!")
        except InvalidPDFError as e:
            print(f"  ✓ Caught InvalidPDFError: {e}")
        except OCRProcessingError as e:
            print(f"  ✓ Caught OCRProcessingError: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")


if __name__ == "__main__":
    basic_ocr_example()
    custom_config_example()
    page_by_page_example()
    error_handling_example()
