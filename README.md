# Property Data Extraction System

A Python-based system for extracting structured property data from unstructured PDF documents using OCR and RAG (Retrieval-Augmented Generation) architecture.

## Features

- **OCR Processing**: Extract text from PDF documents including scanned images
- **RAG Architecture**: Intelligent feature extraction using retrieval and language models
- **RAGAS Evaluation**: Quality metrics for extraction performance
- **Batch Processing**: Process multiple documents in parallel
- **Configurable Pipeline**: Flexible configuration for different document types

## Project Structure

```
property-data-extraction/
├── src/
│   ├── ocr/              # OCR text extraction module
│   ├── chunking/         # Document chunking module
│   ├── vector_store/     # Vector database integration
│   ├── rag/              # RAG extraction engine
│   ├── evaluation/       # RAGAS evaluation module
│   ├── pipeline/         # Pipeline orchestration
│   ├── models/           # Common data models
│   └── config/           # Configuration management
├── tests/                # Test suite
├── data/                 # Data directory (vector store, logs)
├── .env.example          # Example environment variables
├── pyproject.toml        # Project configuration
└── requirements.txt      # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Tesseract OCR (for local OCR processing)

#### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

The system uses a comprehensive configuration management system that supports multiple sources and runtime overrides.

### Quick Start

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
API__OPENAI_API_KEY=your_openai_api_key_here
API__ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

3. Adjust other configuration parameters as needed:
```bash
OCR__DPI=300
CHUNK__CHUNK_SIZE=800
RAG__LLM_MODEL=gpt-4
PIPELINE__BATCH_CONCURRENCY=5
```

### Configuration Options

The system supports multiple configuration sources:

- **Environment Variables**: Use `.env` file with nested delimiter `__`
- **JSON Files**: Use `config.json` for structured configuration
- **Runtime Overrides**: Override settings for specific requests

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete documentation.

### Configuration Sections

- **OCR**: Tesseract settings, DPI, preprocessing options
- **Chunking**: Chunk size, overlap, strategy
- **RAG**: Embedding model, LLM model, temperature, retrieval settings
- **Vector Store**: Persistence directory, collection name, distance metric
- **Pipeline**: Retries, concurrency, rate limiting, timeouts
- **API**: OpenAI and Anthropic API keys
- **Logging**: Log level, file path, format

## Usage

### Single Document Processing

```python
from src.pipeline import ExtractionPipeline
from src.config import get_settings

# Initialize pipeline
settings = get_settings()
pipeline = ExtractionPipeline(settings)

# Process a document
result = pipeline.process_document("path/to/property.pdf")

# Access extracted features
print(result.extraction.features)
print(result.ragas_metrics)
```

### Batch Processing

```python
# Process multiple documents
pdf_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
batch_result = pipeline.process_batch(pdf_paths)

print(f"Processed: {batch_result.successful_documents}/{batch_result.total_documents}")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run property-based tests
pytest -k "property"
```

### Code Formatting

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Architecture

The system follows a multi-stage pipeline architecture:

1. **OCR Module**: Extracts text from PDF documents
2. **Chunking Module**: Splits text into semantic chunks
3. **Vector Store**: Stores chunks as embeddings for retrieval
4. **RAG Engine**: Extracts features using retrieval + generation
5. **Evaluation Module**: Computes RAGAS metrics for quality assessment
6. **Pipeline Orchestrator**: Coordinates the entire workflow

## License

MIT License

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.
