"""Tests for OCR module."""

import pytest
from pathlib import Path
from src.ocr.ocr_module import OCRModule, InvalidPDFError, OCRProcessingError
from src.config.settings import OCRConfig
from src.models.ocr_models import OCRResult


class TestOCRModule:
    """Test suite for OCR module."""

    @pytest.fixture
    def ocr_config(self):
        """Create OCR configuration for testing."""
        return OCRConfig(
            tesseract_cmd="/usr/bin/tesseract",  # Common path on Linux/Mac
            language="eng",
            dpi=300,
            preprocess=True,
            denoise=True,
            deskew=True,
            contrast_enhancement=True
        )

    @pytest.fixture
    def ocr_module(self, ocr_config):
        """Create OCR module instance."""
        return OCRModule(ocr_config)

    def test_ocr_module_initialization(self, ocr_config):
        """Test OCR module initializes correctly."""
        module = OCRModule(ocr_config)
        assert module.config == ocr_config
        assert module.config.language == "eng"
        assert module.config.dpi == 300

    def test_extract_text_invalid_path(self, ocr_module):
        """Test that invalid PDF path raises InvalidPDFError."""
        with pytest.raises(InvalidPDFError, match="PDF file not found"):
            ocr_module.extract_text("nonexistent.pdf")

    def test_extract_text_not_a_file(self, ocr_module, tmp_path):
        """Test that directory path raises InvalidPDFError."""
        with pytest.raises(InvalidPDFError, match="Path is not a file"):
            ocr_module.extract_text(str(tmp_path))

    def test_extract_text_not_pdf(self, ocr_module, tmp_path):
        """Test that non-PDF file raises InvalidPDFError."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("test content")
        
        with pytest.raises(InvalidPDFError, match="File is not a PDF"):
            ocr_module.extract_text(str(text_file))

    def test_extract_text_from_real_pdf(self, ocr_module):
        """Test extracting text from the sample PDF."""
        pdf_path = "monmouth_property.pdf"
        
        # Skip if PDF doesn't exist
        if not Path(pdf_path).exists():
            pytest.skip("Sample PDF not found")
        
        result = ocr_module.extract_text(pdf_path)
        
        # Verify result structure
        assert isinstance(result, OCRResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert len(result.pages) > 0
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.processing_time > 0
        
        # Verify metadata
        assert "pdf_path" in result.metadata
        assert "num_pages" in result.metadata
        assert result.metadata["num_pages"] == len(result.pages)
        
        # Verify page info
        for page in result.pages:
            assert page.page_number > 0
            assert isinstance(page.text, str)
            assert page.confidence >= 0.0
            assert page.confidence <= 1.0
            assert page.width >= 0
            assert page.height >= 0

    def test_page_order_preservation(self, ocr_module):
        """Test that page order is preserved during extraction."""
        pdf_path = "monmouth_property.pdf"
        
        if not Path(pdf_path).exists():
            pytest.skip("Sample PDF not found")
        
        result = ocr_module.extract_text(pdf_path)
        
        # Verify pages are in order
        for i, page in enumerate(result.pages, start=1):
            assert page.page_number == i

    def test_ocr_config_validation(self):
        """Test OCR configuration validation."""
        # Valid config
        config = OCRConfig(dpi=300, language="eng")
        assert config.dpi == 300
        
        # Invalid DPI (too low)
        with pytest.raises(ValueError):
            OCRConfig(dpi=50)
        
        # Invalid DPI (too high)
        with pytest.raises(ValueError):
            OCRConfig(dpi=700)
        
        # Empty language
        with pytest.raises(ValueError):
            OCRConfig(language="")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
