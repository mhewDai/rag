"""OCR module for text extraction from PDFs."""

from src.ocr.ocr_module import InvalidPDFError, OCRError, OCRModule, OCRProcessingError

__all__ = ["OCRModule", "OCRError", "InvalidPDFError", "OCRProcessingError"]
