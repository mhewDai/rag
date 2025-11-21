# RAG Extraction Engine

## Overview

The RAG (Retrieval-Augmented Generation) Extraction Engine is a core component of the Property Data Extraction System that extracts structured property features from unstructured documents using semantic search and large language models (LLMs).

## Architecture

The RAG extraction engine follows a three-stage process:

1. **Query Generation**: Creates feature-specific queries optimized for semantic search
2. **Retrieval**: Fetches relevant document chunks from the vector store
3. **Generation**: Uses an LLM to extract the feature value from retrieved context

```
┌─────────────────┐
│ Feature Schema  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Query Generator │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Store    │◄─── Document Chunks
│ (Semantic       │
│  Search)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Generation  │◄─── Context + Prompt
│ (OpenAI/        │
│  Anthropic)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Value   │
│ + Confidence    │
│ + Sources       │
└─────────────────┘
```

## Key Features

### 1. Multi-LLM Support

The engine supports multiple LLM providers:
- **OpenAI**: GPT-3.5, GPT-4, GPT-4-Turbo
- **Anthropic**: Claude models

The appropriate client is automatically selected based on the model name in the configuration.

### 2. Feature-Specific Query Generation

Queries are dynamically generated for each feature based on:
- Feature name (with underscores replaced by spaces)
- Feature description
- Data type hints (e.g., "price amount dollar" for currency)

This ensures optimal retrieval of relevant document chunks.

### 3. Confidence Scoring

Each extracted value includes a confidence score (0.0 to 1.0) that indicates:
- How clearly the information appears in the source text
- Whether the LLM is certain about the extraction
- If the value meets the configured confidence threshold

Values below the threshold are returned as `null`.

### 4. Source Attribution

Every extraction includes:
- **Source chunks**: The actual text passages used for extraction
- **Source pages**: Page numbers where the information was found

This enables:
- Verification of extracted values
- Debugging extraction issues
- RAGAS evaluation metrics

### 5. Graceful Error Handling

The engine handles errors gracefully:
- Missing features return `null` values with 0.0 confidence
- API failures trigger automatic retry with exponential backoff (up to 3 attempts)
- Invalid JSON responses are caught and return `null`
- Documents not found in vector store raise clear exceptions

### 6. Prompt Engineering

The extraction prompt is carefully designed to:
- Provide clear context about the feature to extract
- Include the feature's data type and requirements
- Request structured JSON output
- Explicitly discourage hallucination
- Request confidence scoring and reasoning

## Usage

### Basic Initialization

```python
from src.rag.extraction_engine import RAGExtractionEngine
from src.vector_store.chroma_store import ChromaVectorStore
from src.config.settings import RAGConfig, VectorStoreConfig

# Configure RAG settings
rag_config = RAGConfig(
    llm_model="gpt-4",
    llm_temperature=0.0,
    top_k_retrieval=5,
    confidence_threshold=0.5,
)

# Initialize vector store
vector_config = VectorStoreConfig()
vector_store = ChromaVectorStore(vector_config)

# Initialize RAG engine
engine = RAGExtractionEngine(
    vector_store=vector_store,
    config=rag_config,
    openai_api_key="your-api-key",
)
```

### Extract Single Feature

```python
from src.models.property_features import get_feature_definition

# Get feature definition
feature = get_feature_definition("owner_name")

# Extract the feature
result = engine.extract_single_feature(
    doc_id="document_123",
    feature=feature,
)

print(f"Value: {result.value}")
print(f"Confidence: {result.confidence}")
print(f"Source pages: {result.source_pages}")
```

### Extract All Features

```python
from src.models.property_features import create_property_feature_schema

# Get complete feature schema
feature_schema = create_property_feature_schema()

# Extract all features
extraction_result = engine.extract_features(
    doc_id="document_123",
    feature_schema=feature_schema,
)

# Access extracted features
for name, feature_value in extraction_result.features.items():
    if feature_value.value is not None:
        print(f"{name}: {feature_value.value} (confidence: {feature_value.confidence})")
```

## Configuration

### RAGConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `embedding_model` | str | "sentence-transformers/all-MiniLM-L6-v2" | Model for generating embeddings |
| `llm_model` | str | "gpt-4" | LLM model name |
| `llm_temperature` | float | 0.0 | Temperature for LLM generation (0.0-2.0) |
| `top_k_retrieval` | int | 5 | Number of chunks to retrieve |
| `max_tokens` | int | 1000 | Maximum tokens for LLM response |
| `confidence_threshold` | float | 0.5 | Minimum confidence to return value |

### Recommended Settings

**For High Accuracy (Production)**:
```python
RAGConfig(
    llm_model="gpt-4",
    llm_temperature=0.0,  # Deterministic
    top_k_retrieval=5,
    confidence_threshold=0.7,  # Higher threshold
)
```

**For Fast Processing (Development)**:
```python
RAGConfig(
    llm_model="gpt-3.5-turbo",
    llm_temperature=0.0,
    top_k_retrieval=3,
    confidence_threshold=0.5,
)
```

**For Exploratory Extraction**:
```python
RAGConfig(
    llm_model="gpt-4",
    llm_temperature=0.3,  # Slightly creative
    top_k_retrieval=7,
    confidence_threshold=0.4,  # Lower threshold
)
```

## Implementation Details

### Query Generation Strategy

The `_generate_query()` method creates optimized queries by:

1. Converting feature names to natural language (e.g., "owner_name" → "owner name")
2. Including the feature description
3. Adding data type hints:
   - Currency: "price amount dollar"
   - Date: "date year month day"
   - Number: "number count quantity"

### LLM Response Parsing

The engine handles various response formats:

1. **Clean JSON**: `{"value": "...", "confidence": 0.95}`
2. **Markdown-wrapped**: ` ```json\n{...}\n``` `
3. **Invalid responses**: Returns `null` with 0.0 confidence

### Retry Logic

API calls use exponential backoff:
- **Attempt 1**: Immediate
- **Attempt 2**: Wait 1 second
- **Attempt 3**: Wait 2 seconds
- **Attempt 4**: Wait 4 seconds (max)

Implemented using the `tenacity` library with `@retry` decorator.

### Value Type Conversion

Extracted values are converted to appropriate types:

- **number**: Converts to `int` if possible, otherwise `float`
- **string**: Converts to `str`
- **currency**: Kept as string (e.g., "$450,000")
- **date**: Kept as string (e.g., "03/15/2023")

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: At least one API key...` | No API keys provided | Set `openai_api_key` or `anthropic_api_key` |
| `ValueError: Document ... not found` | Document not in vector store | Verify document was added with `add_document()` |
| API timeout/rate limit | Too many requests | Reduce `batch_concurrency` or add rate limiting |
| Low confidence scores | Poor document quality or irrelevant chunks | Improve OCR quality or adjust `top_k_retrieval` |

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Extract multiple features in one call using `extract_features()`
2. **Caching**: Consider caching LLM responses for repeated queries
3. **Parallel Extraction**: Process multiple documents concurrently
4. **Chunk Size**: Optimize chunk size (500-1000 tokens) for better retrieval
5. **Top-K Tuning**: Adjust `top_k_retrieval` based on document complexity

### Expected Performance

- **Single feature extraction**: 1-3 seconds (depending on LLM)
- **Full document extraction** (20 features): 20-60 seconds
- **Batch processing**: 10-20 documents per minute (with concurrency)

## Testing

### Unit Tests

Run unit tests with:
```bash
pytest tests/test_rag_engine.py -v
```

Tests cover:
- Initialization with different API keys
- Query generation
- Value type conversion
- Response parsing
- Error handling
- Mock LLM integration

### Integration Tests

Test with real documents:
```bash
python verify_rag_engine.py
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 2.1**: Extracts 20+ property features using feature schema
- **Requirement 2.2**: Returns `null` for missing features (no hallucination)
- **Requirement 3.2**: Retrieves relevant chunks from vector store
- **Requirement 3.3**: Uses LLM for generation with retrieved context
- **Requirement 3.4**: Includes source attribution (chunks and pages)
- **Requirement 3.5**: Provides confidence scores for all extractions

## Future Enhancements

Potential improvements:
1. **Streaming responses**: Support streaming for faster feedback
2. **Multi-modal extraction**: Extract from images and tables
3. **Custom prompts**: Allow per-feature prompt customization
4. **Ensemble methods**: Combine multiple LLM responses
5. **Active learning**: Use low-confidence extractions to improve model

## Related Documentation

- [Property Feature Schema](../src/models/property_features.py)
- [Vector Store Interface](VECTOR_STORE_MODULE.md)
- [Configuration Guide](CONFIGURATION.md)
- [Design Document](../.kiro/specs/property-data-extraction/design.md)
