# Vector Store Module

## Overview

The vector store module provides document embedding storage and semantic search capabilities for the Property Data Extraction System. It uses ChromaDB as the backend and sentence-transformers for generating embeddings.

## Architecture

```
┌─────────────────────────────────────────┐
│         VectorStore Interface           │
│  (Abstract Base Class)                  │
└─────────────────┬───────────────────────┘
                  │
                  │ implements
                  │
┌─────────────────▼───────────────────────┐
│      ChromaVectorStore                  │
│  - ChromaDB client                      │
│  - SentenceTransformer model            │
│  - Embedding generation                 │
│  - Semantic search                      │
└─────────────────────────────────────────┘
```

## Components

### VectorStore Interface

Abstract base class defining the contract for vector store implementations.

**Methods:**
- `add_document(chunks, doc_id)` - Add document with embeddings
- `search(query, top_k, doc_id, filter_metadata)` - Semantic search
- `delete_document(doc_id)` - Remove document
- `update_document(doc_id, chunks)` - Update document
- `document_exists(doc_id)` - Check existence
- `get_document_chunks(doc_id)` - Retrieve chunks
- `clear()` - Clear all documents

### ChromaVectorStore

Concrete implementation using ChromaDB.

**Features:**
- Persistent storage of embeddings
- Automatic embedding generation
- Semantic similarity search
- Document lifecycle management
- Metadata filtering

## Usage

### Basic Usage

```python
from src.vector_store import ChromaVectorStore
from src.models.chunk_models import Chunk
from src.config.settings import VectorStoreConfig, RAGConfig

# Configure
vector_config = VectorStoreConfig(
    persist_directory="./data/chroma",
    collection_name="property_documents",
    distance_metric="cosine"
)

rag_config = RAGConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

# Initialize
vector_store = ChromaVectorStore(vector_config, rag_config)

# Add document
chunks = [
    Chunk(
        text="Property at 123 Main St",
        chunk_id="chunk_1",
        doc_id="doc_001",
        page_number=1,
        start_pos=0,
        end_pos=23
    )
]
doc_id = vector_store.add_document(chunks)

# Search
results = vector_store.search("What is the address?", top_k=5)
for result in results:
    print(f"Score: {result.score}, Text: {result.chunk.text}")

# Delete
vector_store.delete_document(doc_id)
```

### Advanced Search

```python
# Search within specific document
results = vector_store.search(
    query="sale price",
    top_k=3,
    doc_id="doc_001"
)

# Search with metadata filtering
results = vector_store.search(
    query="bedrooms",
    top_k=5,
    filter_metadata={"page_number": 1}
)
```

### Document Lifecycle

```python
# Check if document exists
if vector_store.document_exists("doc_001"):
    # Get all chunks
    chunks = vector_store.get_document_chunks("doc_001")
    
    # Update document
    new_chunks = [...]
    vector_store.update_document("doc_001", new_chunks)
    
    # Delete document
    vector_store.delete_document("doc_001")
```

## Configuration

### VectorStoreConfig

```python
VectorStoreConfig(
    persist_directory="./data/chroma",  # Storage location
    collection_name="documents",        # Collection name
    distance_metric="cosine"            # cosine, euclidean, or dot
)
```

### RAGConfig

```python
RAGConfig(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    top_k_retrieval=5
)
```

## Data Models

### Chunk

```python
@dataclass
class Chunk:
    text: str                           # Chunk text
    chunk_id: str                       # Unique ID
    doc_id: str                         # Document ID
    page_number: int                    # Source page
    start_pos: int                      # Start position
    end_pos: int                        # End position
    embedding: Optional[List[float]]    # Embedding vector
```

### SearchResult

```python
@dataclass
class SearchResult:
    chunk: Chunk                        # Retrieved chunk
    score: float                        # Similarity score
    metadata: Dict[str, Any]            # Additional metadata
```

## Error Handling

### VectorStoreError

Custom exception for vector store operations.

```python
try:
    vector_store.add_document([])
except VectorStoreError as e:
    print(f"Error: {e}")
    if e.cause:
        print(f"Caused by: {e.cause}")
```

### Common Errors

- Empty chunks list
- Empty search query
- Invalid top_k value (< 1)
- Non-existent document
- Embedding generation failure
- ChromaDB connection issues

## Performance Considerations

### Embedding Generation

- Embeddings are generated in batches for efficiency
- First document add may be slower (model loading)
- Subsequent operations use cached model

### Search Performance

- Search time scales with collection size
- Use `doc_id` filter to restrict search scope
- Use metadata filters to narrow results
- Consider top_k value (smaller = faster)

### Storage

- ChromaDB persists to disk automatically
- Storage grows with number of documents
- Use `clear()` to reset collection

## Best Practices

1. **Batch Operations**: Add multiple chunks at once when possible
2. **Consistent IDs**: Use meaningful, consistent document IDs
3. **Metadata**: Include relevant metadata for filtering
4. **Error Handling**: Always wrap operations in try-except
5. **Cleanup**: Delete documents when no longer needed
6. **Configuration**: Use appropriate embedding model for your use case

## Integration with Pipeline

The vector store integrates with the extraction pipeline:

1. **OCR Module** → Extracts text from PDF
2. **Chunking Module** → Splits text into chunks
3. **Vector Store** → Stores chunks with embeddings
4. **RAG Engine** → Retrieves relevant chunks for extraction

## Testing

### Unit Tests

See `tests/test_vector_store.py` (to be created in future tasks)

### Verification

Run `python verify_vector_store.py` to test all operations.

### Example

Run `python examples/vector_store_usage.py` for usage demonstration.

## Dependencies

- `chromadb>=0.4.0` - Vector database
- `sentence-transformers>=2.2.0` - Embedding generation
- `numpy>=1.24.0` - Numerical operations

## Future Enhancements

- Support for FAISS backend
- Support for Pinecone backend
- Batch embedding optimization
- Async operations
- Embedding caching
- Index optimization
- Multi-collection support

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- Design Document: `.kiro/specs/property-data-extraction/design.md`
- Requirements: `.kiro/specs/property-data-extraction/requirements.md`
