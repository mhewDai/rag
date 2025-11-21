"""Vector store module for document embedding and semantic search."""

from src.vector_store.vector_store import (
    VectorStore,
    VectorStoreError,
    SearchResult
)
from src.vector_store.chroma_store import ChromaVectorStore

__all__ = [
    "VectorStore",
    "VectorStoreError",
    "SearchResult",
    "ChromaVectorStore"
]
