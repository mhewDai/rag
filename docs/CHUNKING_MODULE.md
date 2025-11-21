# Document Chunking Module

## Overview

The Document Chunking Module provides intelligent text segmentation for the Property Data Extraction System. It splits extracted text into semantically meaningful chunks with configurable overlap, using sentence-aware splitting to maintain context for downstream retrieval and extraction tasks.

## Features

- **Sentence-Aware Splitting**: Respects sentence boundaries to create semantically coherent chunks
- **Sliding Window with Overlap**: Configurable overlap between chunks to preserve context
- **Edge Case Handling**: Gracefully handles empty documents, very short text, and single sentences
- **Runtime Configuration**: Supports both instance-level and per-request configuration
- **Position Tracking**: Maintains start and end positions for each chunk in the original text
- **Page Metadata**: Preserves page number information for multi-page documents

## Architecture

### DocumentChunker Class

The `DocumentChunker` class is the main interface for text chunking operations.

```python
from src.chunking import DocumentChunker
from src.config.settings import ChunkConfig

# Create chunker with default config
chunker = DocumentChunker()

# Or with custom config
config = ChunkConfig(chunk_size=500, chunk_overlap=50)
chunker = DocumentChunker(config)
```

### Chunk Data Model

Each chunk is represented by the `Chunk` dataclass:

```python
@dataclass
class Chunk:
    text: str                      # The chunk text content
    chunk_id: str                  # Unique identifier
    doc_id: str                    # Parent document ID
    page_number: int               # Page number in source document
    start_pos: int                 # Starting position in original text
    end_pos: int                   # Ending position in original text
    embedding: Optional[List[float]]  # Vector embedding (populated later)
```

## Configuration

### ChunkConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | int | 800 | Maximum chunk size in characters |
| `chunk_overlap` | int | 100 | Overlap between chunks in characters |
| `strategy` | str | "sentence-aware" | Chunking strategy |
| `min_chunk_size` | int | 50 | Minimum chunk size in characters |

### Configuration Validation

- `chunk_overlap` must be less than `chunk_size`
- `min_chunk_size` must be less than or equal to `chunk_size`
- `chunk_size` must be between 100 and 2000
- `chunk_overlap` must be between 0 and 500

## Usage

### Basic Chunking

```python
from src.chunking import DocumentChunker

chunker = DocumentChunker()
text = "Your document text here. Multiple sentences work best."
chunks = chunker.chunk_document(text, doc_id="doc_001", page_number=1)

for chunk in chunks:
    print(f"Chunk {chunk.chunk_id}: {chunk.text}")
```

### Custom Configuration

```python
from src.chunking import DocumentChunker
from src.config.settings import ChunkConfig

# Create custom configuration
config = ChunkConfig(
    chunk_size=500,
    chunk_overlap=75,
    min_chunk_size=30
)

chunker = DocumentChunker(config)
chunks = chunker.chunk_document(text, doc_id="doc_002")
```

### Runtime Configuration Override

```python
# Create chunker with default config
chunker = DocumentChunker()

# Override config for specific request
override_config = ChunkConfig(chunk_size=300, chunk_overlap=50)
chunks = chunker.chunk_document(
    text, 
    doc_id="doc_003",
    config=override_config
)
```

### Multi-Page Documents

```python
chunker = DocumentChunker()

# Process each page separately
for page_num, page_text in enumerate(pages, start=1):
    chunks = chunker.chunk_document(
        page_text,
        doc_id="multi_page_doc",
        page_number=page_num
    )
    # Process chunks...
```

## Chunking Algorithm

### Sentence-Aware Splitting

1. **Text Preprocessing**: Trim whitespace and validate input
2. **Sentence Detection**: Split text using regex patterns that detect sentence boundaries (. ! ?)
3. **Chunk Building**: Accumulate sentences until chunk_size is reached
4. **Overlap Management**: Keep sentences that fit within overlap size for next chunk
5. **Position Tracking**: Record start and end positions in original text

### Edge Case Handling

| Case | Behavior |
|------|----------|
| Empty text | Returns empty list |
| Whitespace only | Returns empty list |
| Text < min_chunk_size | Returns single chunk with all text |
| Single sentence | Returns single chunk (or splits by character if too long) |
| Very long sentence | Falls back to character-based splitting |

### Sentence Splitting Logic

The module uses regex patterns to detect sentence boundaries:

```python
# Pattern matches: . ! ? followed by space and capital letter, or end of string
sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
```

This approach:
- Handles common sentence endings (. ! ?)
- Avoids false positives from abbreviations (when followed by lowercase)
- Respects paragraph boundaries

## Integration with Pipeline

The chunking module integrates with the extraction pipeline:

```
OCR Module → Text Extraction
     ↓
Document Chunker → Text Segmentation
     ↓
Vector Store → Embedding & Storage
     ↓
RAG Engine → Feature Extraction
```

### Example Pipeline Integration

```python
from src.ocr import OCRModule
from src.chunking import DocumentChunker
from src.config.settings import get_settings

# Get configuration
settings = get_settings()

# Extract text from PDF
ocr = OCRModule(settings.ocr)
ocr_result = ocr.extract_text("property.pdf")

# Chunk the extracted text
chunker = DocumentChunker(settings.chunk)
all_chunks = []

for page in ocr_result.pages:
    chunks = chunker.chunk_document(
        page.text,
        doc_id=ocr_result.metadata.get("doc_id", "unknown"),
        page_number=page.page_number
    )
    all_chunks.extend(chunks)

# Continue with embedding and storage...
```

## Performance Considerations

### Chunk Size Selection

- **Smaller chunks (200-400 chars)**: Better precision, more chunks to process
- **Medium chunks (500-800 chars)**: Balanced approach, recommended for most use cases
- **Larger chunks (1000-1500 chars)**: Better context, fewer chunks, may reduce precision

### Overlap Selection

- **Small overlap (20-50 chars)**: Minimal redundancy, faster processing
- **Medium overlap (75-150 chars)**: Recommended for sentence-aware chunking
- **Large overlap (200+ chars)**: Maximum context preservation, more redundancy

### Memory Usage

- Each chunk stores: text, metadata, and optional embedding vector
- For large documents: Consider processing pages separately
- Embeddings are populated later by the vector store module

## Testing

The module includes comprehensive tests:

```bash
# Run chunking tests
python -m pytest tests/test_chunking.py -v

# Run verification script
python verify_chunking.py

# Run usage examples
python examples/chunking_usage.py
```

## Error Handling

The chunker handles errors gracefully:

- **Invalid input**: Returns empty list for empty/whitespace text
- **Configuration errors**: Raises `ValueError` with descriptive message
- **Edge cases**: Automatically adjusts strategy (e.g., character-based for long sentences)

## Requirements Validation

This implementation satisfies **Requirement 3.1**:

> WHEN OCR text is available THEN the RAG System SHALL chunk the text into semantically meaningful segments for retrieval

The module:
- ✅ Chunks text into semantically meaningful segments (sentence-aware)
- ✅ Supports configurable chunk sizes and overlap
- ✅ Preserves metadata (page numbers, positions)
- ✅ Handles edge cases gracefully
- ✅ Integrates with pipeline configuration system

## Future Enhancements

Potential improvements for future versions:

1. **Semantic Chunking**: Use embeddings to detect topic boundaries
2. **Table Detection**: Special handling for tabular data
3. **Multi-Language Support**: Language-specific sentence detection
4. **Adaptive Chunking**: Automatically adjust chunk size based on content
5. **Chunk Quality Metrics**: Score chunks based on semantic coherence

## API Reference

### DocumentChunker

#### `__init__(config: Optional[ChunkConfig] = None)`

Initialize the document chunker.

**Parameters:**
- `config`: Optional chunking configuration. Uses defaults if not provided.

#### `chunk_document(text: str, doc_id: str, page_number: int = 1, config: Optional[ChunkConfig] = None) -> List[Chunk]`

Split document into overlapping chunks with sentence-aware splitting.

**Parameters:**
- `text`: Extracted text from OCR or other source
- `doc_id`: Document identifier
- `page_number`: Page number for metadata (default: 1)
- `config`: Optional runtime configuration override

**Returns:**
- List of Chunk objects with text, metadata, and position info

**Example:**
```python
chunks = chunker.chunk_document(
    text="Your text here.",
    doc_id="doc_123",
    page_number=1
)
```

## See Also

- [Configuration Documentation](CONFIGURATION.md)
- [OCR Module Documentation](OCR_MODULE.md)
- [Pipeline Documentation](PIPELINE.md)
