"""Simple script to verify OCR module implementation."""

from pathlib import Path
from src.ocr.ocr_module import OCRModule, InvalidPDFError
from src.config.settings import OCRConfig


def main():
    """Verify OCR module works correctly."""
    print("=" * 60)
    print("OCR Module Verification")
    print("=" * 60)
    
    # Create OCR configuration
    config = OCRConfig(
        tesseract_cmd="/usr/bin/tesseract",
        language="eng",
        dpi=300,
        preprocess=True
    )
    print(f"\n✓ OCR Config created: language={config.language}, dpi={config.dpi}")
    
    # Initialize OCR module
    ocr_module = OCRModule(config)
    print("✓ OCR Module initialized")
    
    # Test invalid file handling
    try:
        ocr_module.extract_text("nonexistent.pdf")
        print("✗ Should have raised InvalidPDFError for nonexistent file")
    except InvalidPDFError as e:
        print(f"✓ Correctly raised InvalidPDFError: {e}")
    
    # Test with sample PDF if it exists
    pdf_path = "monmouth_property.pdf"
    if Path(pdf_path).exists():
        print(f"\n✓ Found sample PDF: {pdf_path}")
        print("  Extracting text (this may take a moment)...")
        
        try:
            result = ocr_module.extract_text(pdf_path)
            
            print(f"\n✓ OCR extraction successful!")
            print(f"  - Pages processed: {len(result.pages)}")
            print(f"  - Total text length: {len(result.text)} characters")
            print(f"  - Overall confidence: {result.confidence:.2%}")
            print(f"  - Processing time: {result.processing_time:.2f} seconds")
            
            # Show page details
            print(f"\n  Page details:")
            for page in result.pages[:3]:  # Show first 3 pages
                print(f"    Page {page.page_number}: {len(page.text)} chars, "
                      f"confidence: {page.confidence:.2%}, "
                      f"size: {page.width}x{page.height}")
            
            if len(result.pages) > 3:
                print(f"    ... and {len(result.pages) - 3} more pages")
            
            # Show sample text
            sample_text = result.text[:200].replace('\n', ' ')
            print(f"\n  Sample text: {sample_text}...")
            
            print("\n✓ All verifications passed!")
            
        except Exception as e:
            print(f"\n✗ OCR extraction failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n⚠ Sample PDF not found: {pdf_path}")
        print("  Skipping extraction test")
    
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
