"""Data models for OCR processing."""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class PageInfo:
    """Information about a single page in a PDF."""

    page_number: int
    text: str
    confidence: float
    width: int
    height: int


@dataclass
class OCRResult:
    """Result of OCR text extraction."""

    text: str
    pages: List[PageInfo]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
