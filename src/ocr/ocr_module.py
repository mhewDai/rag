"""OCR module for text extraction from PDF documents."""

import logging
import time
from pathlib import Path
from typing import List

import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
from PyPDF2 import PdfReader

from src.config.settings import OCRConfig
from src.models.ocr_models import OCRResult, PageInfo

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Base exception for OCR-related errors."""

    pass


class InvalidPDFError(OCRError):
    """Raised when PDF is corrupted or invalid."""

    pass


class OCRProcessingError(OCRError):
    """Raised when OCR processing fails."""

    pass


class OCRModule:
    """
    OCR module for extracting text from PDF documents.

    Handles both text-based and scanned PDFs with image preprocessing
    and confidence scoring.
    """

    def __init__(self, config: OCRConfig):
        """
        Initialize OCR module with configuration.

        Args:
            config: OCR configuration settings
        """
        self.config = config

        # Set Tesseract command path
        if self.config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd

        logger.info(f"OCR module initialized with language: {config.language}, DPI: {config.dpi}")

    def extract_text(self, pdf_path: str) -> OCRResult:
        """
        Extract text from PDF document.

        This method handles both text-based PDFs and scanned image PDFs.
        For scanned documents, it converts pages to images and applies OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            OCRResult containing extracted text, page metadata, and confidence scores

        Raises:
            InvalidPDFError: If PDF is corrupted or unreadable
            OCRProcessingError: If OCR processing fails
        """
        start_time = time.time()

        # Validate PDF file
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise InvalidPDFError(f"PDF file not found: {pdf_path}")

        if not pdf_file.is_file():
            raise InvalidPDFError(f"Path is not a file: {pdf_path}")

        if pdf_file.suffix.lower() != '.pdf':
            raise InvalidPDFError(f"File is not a PDF: {pdf_path}")

        try:
            # First, try to extract text directly from PDF (for text-based PDFs)
            pages_info = self._extract_text_from_pdf(pdf_path)

            # If no text was extracted, treat as scanned PDF
            total_text = "".join(page.text for page in pages_info)
            if not total_text.strip():
                logger.info(f"No text found in PDF, treating as scanned document: {pdf_path}")
                pages_info = self._extract_text_from_images(pdf_path)

            # Calculate overall confidence
            if pages_info:
                overall_confidence = sum(page.confidence for page in pages_info) / len(pages_info)
            else:
                overall_confidence = 0.0

            # Combine all page text
            full_text = "\n\n".join(page.text for page in pages_info)

            processing_time = time.time() - start_time

            result = OCRResult(
                text=full_text,
                pages=pages_info,
                confidence=overall_confidence,
                processing_time=processing_time,
                metadata={
                    "pdf_path": str(pdf_path),
                    "num_pages": len(pages_info),
                    "ocr_language": self.config.language,
                    "dpi": self.config.dpi,
                    "preprocessing_enabled": self.config.preprocess,
                }
            )

            logger.info(
                f"OCR completed for {pdf_path}: {len(pages_info)} pages, "
                f"confidence: {overall_confidence:.2f}, time: {processing_time:.2f}s"
            )

            return result

        except InvalidPDFError:
            raise
        except Exception as e:
            logger.error(f"OCR processing failed for {pdf_path}: {str(e)}")
            raise OCRProcessingError(f"Failed to process PDF: {str(e)}") from e

    def _extract_text_from_pdf(self, pdf_path: str) -> List[PageInfo]:
        """
        Extract text directly from PDF (for text-based PDFs).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PageInfo objects with extracted text

        Raises:
            InvalidPDFError: If PDF cannot be read
        """
        try:
            reader = PdfReader(pdf_path)
            pages_info = []

            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""

                    # Get page dimensions if available
                    width = int(page.mediabox.width) if page.mediabox else 0
                    height = int(page.mediabox.height) if page.mediabox else 0

                    # For text-based PDFs, confidence is high
                    confidence = 1.0 if text.strip() else 0.0

                    page_info = PageInfo(
                        page_number=page_num,
                        text=text,
                        confidence=confidence,
                        width=width,
                        height=height
                    )
                    pages_info.append(page_info)

                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                    # Add empty page info
                    pages_info.append(PageInfo(
                        page_number=page_num,
                        text="",
                        confidence=0.0,
                        width=0,
                        height=0
                    ))

            return pages_info

        except Exception as e:
            raise InvalidPDFError(f"Cannot read PDF file: {str(e)}") from e

    def _extract_text_from_images(self, pdf_path: str) -> List[PageInfo]:
        """
        Extract text from PDF by converting to images and applying OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PageInfo objects with OCR-extracted text

        Raises:
            OCRProcessingError: If image conversion or OCR fails
        """
        try:
            # Convert PDF pages to images
            images = convert_from_path(
                pdf_path,
                dpi=self.config.dpi,
                fmt='png'
            )

            pages_info = []

            for page_num, image in enumerate(images, start=1):
                try:
                    # Preprocess image if enabled
                    if self.config.preprocess:
                        image = self._preprocess_image(image)

                    # Extract text with confidence data
                    ocr_data = pytesseract.image_to_data(
                        image,
                        lang=self.config.language,
                        output_type=pytesseract.Output.DICT
                    )

                    # Extract text
                    text = pytesseract.image_to_string(
                        image,
                        lang=self.config.language
                    )

                    # Calculate average confidence
                    confidences = [
                        float(conf) for conf in ocr_data['conf']
                        if conf != -1  # -1 indicates no text detected
                    ]
                    avg_confidence = (
                        sum(confidences) / len(confidences) / 100.0
                        if confidences else 0.0
                    )

                    page_info = PageInfo(
                        page_number=page_num,
                        text=text,
                        confidence=avg_confidence,
                        width=image.width,
                        height=image.height
                    )
                    pages_info.append(page_info)

                    logger.debug(
                        f"Processed page {page_num}: {len(text)} chars, "
                        f"confidence: {avg_confidence:.2f}"
                    )

                except Exception as e:
                    logger.error(f"OCR failed for page {page_num}: {str(e)}")
                    # Add empty page info for failed pages
                    pages_info.append(PageInfo(
                        page_number=page_num,
                        text="",
                        confidence=0.0,
                        width=0,
                        height=0
                    ))

            return pages_info

        except Exception as e:
            raise OCRProcessingError(f"Failed to convert PDF to images: {str(e)}") from e

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.

        Applies deskewing, denoising, and contrast enhancement based on config.

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image object
        """
        try:
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')

            # Denoise
            if self.config.denoise:
                image = image.filter(ImageFilter.MedianFilter(size=3))

            # Enhance contrast
            if self.config.contrast_enhancement:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)

            # Deskew
            if self.config.deskew:
                image = self._deskew_image(image)

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}, using original image")
            return image

    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """
        Deskew image to correct rotation.

        Uses Tesseract's OSD (Orientation and Script Detection) to detect
        and correct image rotation.

        Args:
            image: PIL Image object

        Returns:
            Deskewed PIL Image object
        """
        try:
            # Try to detect orientation
            osd = pytesseract.image_to_osd(image)

            # Parse rotation angle from OSD output
            rotation_angle = 0
            for line in osd.split('\n'):
                if 'Rotate:' in line:
                    rotation_angle = int(line.split(':')[1].strip())
                    break

            # Rotate image if needed
            if rotation_angle != 0:
                image = image.rotate(-rotation_angle, expand=True, fillcolor='white')
                logger.debug(f"Deskewed image by {rotation_angle} degrees")

            return image

        except Exception as e:
            # If deskewing fails, return original image
            logger.debug(f"Deskewing failed: {str(e)}, using original image")
            return image

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image file.

        Utility method for processing individual images.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text

        Raises:
            OCRProcessingError: If image processing fails
        """
        try:
            image = Image.open(image_path)

            if self.config.preprocess:
                image = self._preprocess_image(image)

            text = pytesseract.image_to_string(
                image,
                lang=self.config.language
            )

            return text

        except Exception as e:
            raise OCRProcessingError(f"Failed to process image: {str(e)}") from e
