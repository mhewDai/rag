"""Vector store module for document embedding and semantic search."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import uuid
from dataclasses import dataclass

from src.models.chunk_models import Chunk


@dataclass
class SearchResult:
    """Result from vector store search."""
    
    chunk: Chunk
    score: float
    metadata: Dict[str, Any]


class VectorStore(ABC):
    """
    Abstract interface for vector store operations.
    
    This interface defines the contract for vector store implementations,
    allowing different backends (ChromaDB, FAISS, Pinecone) to be used
    interchangeably.
    """
    
    @abstractmethod
    def add_document(
        self, 
        chunks: List[Chunk], 
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add document chunks to vector store with embeddings.
        
        Args:
            chunks: List of Chunk objects to add
            doc_id: Optional document identifier. If None, generates UUID.
            
        Returns:
            Document ID for the added document
            
        Raises:
            VectorStoreError: If adding document fails
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        doc_id: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for relevant chunks using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            doc_id: Optional document ID to restrict search
            filter_metadata: Optional metadata filters
            
        Returns:
            List of SearchResult objects ordered by relevance
            
        Raises:
            VectorStoreError: If search fails
        """
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """
        Remove document and all its chunks from vector store.
        
        Args:
            doc_id: Document identifier to delete
            
        Returns:
            True if document was deleted, False if not found
            
        Raises:
            VectorStoreError: If deletion fails
        """
        pass
    
    @abstractmethod
    def update_document(
        self, 
        doc_id: str, 
        chunks: List[Chunk]
    ) -> bool:
        """
        Update an existing document with new chunks.
        
        This deletes the old document and adds the new chunks.
        
        Args:
            doc_id: Document identifier to update
            chunks: New chunks to replace existing ones
            
        Returns:
            True if document was updated, False if not found
            
        Raises:
            VectorStoreError: If update fails
        """
        pass
    
    @abstractmethod
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists in the vector store.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_document_chunks(self, doc_id: str) -> List[Chunk]:
        """
        Retrieve all chunks for a specific document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of Chunk objects for the document
            
        Raises:
            VectorStoreError: If document not found or retrieval fails
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear all documents from the vector store.
        
        Raises:
            VectorStoreError: If clearing fails
        """
        pass


class VectorStoreError(Exception):
    """Exception raised for vector store operation errors."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        """
        Initialize vector store error.
        
        Args:
            message: Error message
            cause: Optional underlying exception
        """
        super().__init__(message)
        self.cause = cause
