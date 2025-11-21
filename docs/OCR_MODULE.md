# OCR Module Documentation

## Overview

The OCR (Optical Character Recognition) module extracts text from PDF documents, handling both text-based PDFs and scanned image PDFs. It provides robust error handling, image preprocessing, and confidence scoring.

## Features

- **Dual PDF Processing**: Handles both text-based and scanned PDFs
- **Image Preprocessing**: Deskewing, denoising, and contrast enhancement
- **Confidence Scoring**: Per-page and overall confidence metrics
- **Page Metadata**: Tracks page numbers, dimensions, and positions
- **Error Handling**: Comprehensive error handling for corrupted or invalid PDFs
- **Configurable**: Flexible configuration for different document types

## Requirements

The OCR module requires the following dependencies:

- `pytesseract>=0.3.10` - Python wrapper for Tesseract OCR
- `pdf2image>=1.16.3` - PDF to image conversion
- `Pillow>=10.0.0` - Image processing
- `PyPDF2>=3.0.0` - PDF text extraction

Additionally, Tesseract OCR must be installed on the system:

- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Configuration

The OCR module is configured using the `OCRConfig` class:

```python
from src.config.settings import OCRConfig

config = OCRConfig(
    tesseract_cmd="/usr/bin/tesseract",  # Path to Tesseract executable
    language="eng",                       # OCR language code
    dpi=300,                             # DPI for image processing (72-600)
    preprocess=True,                     # Enable image preprocessing
    denoise=True,                        # Enable denoising
    deskew=True,                         # Enable deskewing
    contrast_enhancement=True            # Enable contrast enhancement
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tesseract_cmd` | str | `/usr/local/bin/tesseract` | Path to Tesseract executable |
| `language` | str | `eng` | OCR language code (e.g., 'eng', 'spa', 'fra') |
| `dpi` | int | `300` | DPI for image processing (72-600) |
| `preprocess` | bool | `True` | Enable image preprocessing |
| `denoise` | bool | `True` | Enable denoising filter |
| `deskew` | bool | `True` | Enable automatic deskewing |
| `contrast_enhancement` | bool | `True` | Enable contrast enhancement |

## Usage

### Basic Usage

```python
from src.ocr import OCRModule
from src.config.settings import OCRConfig

# Create configuration
config = OCRConfig(language="eng", dpi=300)

# Initialize OCR module
ocr = OCRModule(config)

# Extract text from PDF
result = ocr.extract_text("document.pdf")

# Access results
print(f"Extracted text: {result.text}")
print(f"Number of pages: {len(result.pages)}")
print(f"Confidence: {result.confidence:.2%}")
```

### Processing Individual Pages

```python
result = ocr.extract_text("document.pdf")

for page in result.pages:
    print(f"Page {page.page_number}:")
    print(f"  Text: {page.text[:100]}...")
    print(f"  Confidence: {page.confidence:.2%}")
    print(f"  Dimensions: {page.width}x{page.height}")
```

### Error Handling

```python
from src.ocr import OCRModule, InvalidPDFError, OCRProcessingError

try:
    result = ocr.extract_text("document.pdf")
except InvalidPDFError as e:
    print(f"Invalid PDF: {e}")
except OCRProcessingError as e:
    print(f"Processing failed: {e}")
```

### Custom Configuration for Different Document Types

#### High-Quality Scanned Documents

```python
config = OCRConfig(
    dpi=600,              # Higher DPI for better quality
    preprocess=True,
    denoise=False,        # Clean scans don't need denoising
    deskew=True,
    contrast_enhancement=False
)
```

#### Low-Quality or Degraded Documents

```python
config = OCRConfig(
    dpi=300,
    preprocess=True,
    denoise=True,         # Remove noise from degraded scans
    deskew=True,
    contrast_enhancement=True  # Enhance faded text
)
```

#### Text-Based PDFs (No Scanning)

```python
config = OCRConfig(
    preprocess=False,     # No preprocessing needed
    dpi=150              # Lower DPI sufficient for text extraction
)
```

## API Reference

### OCRModule

Main class for OCR processing.

#### `__init__(config: OCRConfig)`

Initialize OCR module with configuration.

**Parameters:**
- `config` (OCRConfig): OCR configuration settings

#### `extract_text(pdf_path: str) -> OCRResult`

Extract text from PDF document.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `OCRResult`: Extraction result with text, pages, confidence, and metadata

**Raises:**
- `InvalidPDFError`: If PDF is corrupted or unreadable
- `OCRProcessingError`: If OCR processing fails

#### `extract_text_from_image(image_path: str) -> str`

Extract text from a single image file.

**Parameters:**
- `image_path` (str): Path to image file

**Returns:**
- `str`: Extracted text

**Raises:**
- `OCRProcessingError`: If image processing fails

### Data Models

#### OCRResult

```python
@dataclass
class OCRResult:
    text: str                      # Combined text from all pages
    pages: List[PageInfo]          # Per-page information
    confidence: float              # Overall confidence (0.0-1.0)
    processing_time: float         # Processing time in seconds
    metadata: Dict[str, Any]       # Additional metadata
```

#### PageInfo

```python
@dataclass
class PageInfo:
    page_number: int               # Page number (1-indexed)
    text: str                      # Extracted text
    confidence: float              # Page confidence (0.0-1.0)
    width: int                     # Page width in pixels
    height: int                    # Page height in pixels
```

### Exceptions

#### `OCRError`

Base exception for OCR-related errors.

#### `InvalidPDFError`

Raised when PDF is corrupted, unreadable, or invalid.

#### `OCRProcessingError`

Raised when OCR processing fails.

## Image Preprocessing

The OCR module applies several preprocessing steps to improve text extraction accuracy:

### 1. Grayscale Conversion

Converts color images to grayscale for better OCR performance.

### 2. Denoising

Applies a median filter to remove noise from scanned images. Particularly useful for:
- Low-quality scans
- Photocopied documents
- Documents with background texture

### 3. Contrast Enhancement

Enhances contrast to make text more readable. Helpful for:
- Faded documents
- Low-contrast scans
- Documents with poor lighting

### 4. Deskewing

Automatically detects and corrects image rotation using Tesseract's OSD (Orientation and Script Detection). Corrects:
- Skewed scans
- Rotated pages
- Misaligned documents

## Performance Considerations

### Processing Speed

- **Text-based PDFs**: Very fast (~0.1-0.5s per page)
- **Scanned PDFs**: Slower (~2-5s per page depending on DPI and preprocessing)

### DPI Settings

- **72-150 DPI**: Fast but lower accuracy
- **300 DPI**: Good balance (recommended)
- **600 DPI**: High accuracy but slower

### Memory Usage

- Higher DPI increases memory usage
- Large multi-page PDFs may require significant memory
- Consider processing pages in batches for very large documents

## Troubleshooting

### Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solution**: Install Tesseract and set correct path in config:
```python
config = OCRConfig(tesseract_cmd="/usr/bin/tesseract")
```

### Low Confidence Scores

**Causes**:
- Poor scan quality
- Incorrect language setting
- Handwritten text (not supported)

**Solutions**:
- Increase DPI to 600
- Enable all preprocessing options
- Verify correct language code
- Rescan document at higher quality

### Empty Text Extraction

**Causes**:
- PDF is image-only without embedded text
- Incorrect language setting
- Severely degraded document

**Solutions**:
- Ensure preprocessing is enabled
- Try different language codes
- Manually verify PDF is readable

### Slow Processing

**Causes**:
- High DPI setting
- Large documents
- All preprocessing enabled

**Solutions**:
- Reduce DPI to 300
- Disable unnecessary preprocessing
- Process pages in parallel (future enhancement)

## Examples

See `examples/ocr_usage.py` for complete working examples:

- Basic OCR extraction
- Custom configuration
- Page-by-page processing
- Error handling

## Testing

Run the OCR module tests:

```bash
pytest tests/test_ocr.py -v
```

Verify OCR module installation:

```bash
python verify_ocr.py
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 1.1**: Extracts all text content from PDF documents
- **Requirement 1.2**: Processes images and scanned pages
- **Requirement 1.3**: Preserves extracted text for downstream processing
- **Requirement 1.4**: Returns error messages for corrupted/invalid PDFs
- **Requirement 1.5**: Processes all pages and maintains page order

## Future Enhancements

- Multi-language support with automatic detection
- Parallel page processing for faster extraction
- Table detection and structured extraction
- Handwriting recognition support
- Cloud OCR service integration (Google Vision, AWS Textract)
