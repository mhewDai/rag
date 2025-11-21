"""Vector store module for document embedding and semantic search."""

from src.vector_store.chroma_store import ChromaVectorStore
from src.vector_store.vector_store import SearchResult, VectorStore, VectorStoreError

__all__ = [
    "VectorStore",
    "VectorStoreError",
    "SearchResult",
    "ChromaVectorStore"
]
