"""ChromaDB implementation of vector store."""

import logging
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "ChromaDB dependencies not installed. "
        "Install with: pip install chromadb sentence-transformers"
    ) from e

from src.config.settings import RAGConfig, VectorStoreConfig
from src.models.chunk_models import Chunk
from src.vector_store.vector_store import SearchResult, VectorStore, VectorStoreError

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    """
    ChromaDB implementation of vector store.

    This class provides document embedding, storage, and semantic search
    using ChromaDB as the backend and sentence-transformers for embeddings.
    """

    def __init__(
        self,
        vector_config: VectorStoreConfig,
        rag_config: RAGConfig
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            vector_config: Vector store configuration
            rag_config: RAG configuration (for embedding model)
        """
        self.vector_config = vector_config
        self.rag_config = rag_config

        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {rag_config.embedding_model}")
            self.embedding_model = SentenceTransformer(rag_config.embedding_model)
        except Exception as e:
            raise VectorStoreError(
                f"Failed to load embedding model '{rag_config.embedding_model}'",
                cause=e
            )

        # Initialize ChromaDB client
        try:
            logger.info(f"Initializing ChromaDB at: {vector_config.persist_directory}")
            self.client = chromadb.PersistentClient(
                path=vector_config.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=vector_config.collection_name,
                metadata={"hnsw:space": vector_config.distance_metric}
            )

            logger.info(
                f"ChromaDB initialized with collection: {vector_config.collection_name}"
            )

        except Exception as e:
            raise VectorStoreError(
                "Failed to initialize ChromaDB client",
                cause=e
            )

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            VectorStoreError: If embedding generation fails
        """
        try:
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            raise VectorStoreError(
                f"Failed to generate embeddings for {len(texts)} texts",
                cause=e
            )

    def add_document(
        self,
        chunks: List[Chunk],
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add document chunks to vector store with embeddings.

        Args:
            chunks: List of Chunk objects to add
            doc_id: Optional document identifier. If None, uses doc_id from chunks.

        Returns:
            Document ID for the added document

        Raises:
            VectorStoreError: If adding document fails
        """
        if not chunks:
            raise VectorStoreError("Cannot add document with empty chunks list")

        # Use provided doc_id or get from first chunk
        document_id = doc_id or chunks[0].doc_id

        try:
            # Extract texts for embedding
            texts = [chunk.text for chunk in chunks]

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = self._generate_embeddings(texts)

            # Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding

            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [
                {
                    "doc_id": chunk.doc_id,
                    "page_number": chunk.page_number,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    "chunk_id": chunk.chunk_id
                }
                for chunk in chunks
            ]

            # Add to collection
            logger.info(f"Adding {len(chunks)} chunks to ChromaDB for doc: {document_id}")
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Successfully added document {document_id} with {len(chunks)} chunks")
            return document_id

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to add document {document_id}",
                cause=e
            )

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
        if not query or not query.strip():
            raise VectorStoreError("Search query cannot be empty")

        if top_k < 1:
            raise VectorStoreError("top_k must be at least 1")

        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query[:50]}...")
            query_embedding = self._generate_embeddings([query])[0]

            # Build where clause for filtering
            where_clause = filter_metadata or {}
            if doc_id:
                where_clause["doc_id"] = doc_id

            # Perform search
            logger.debug(f"Searching for top {top_k} results")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None
            )

            # Parse results into SearchResult objects
            search_results = []

            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    chunk_id = results['ids'][0][i]
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if 'distances' in results else 0.0

                    # Convert distance to similarity score (1 - distance for cosine)
                    score = 1.0 - distance if distance is not None else 1.0

                    # Reconstruct Chunk object
                    chunk = Chunk(
                        text=document,
                        chunk_id=chunk_id,
                        doc_id=metadata.get('doc_id', ''),
                        page_number=metadata.get('page_number', 0),
                        start_pos=metadata.get('start_pos', 0),
                        end_pos=metadata.get('end_pos', 0),
                        embedding=None  # Don't include embedding in search results
                    )

                    search_results.append(
                        SearchResult(
                            chunk=chunk,
                            score=score,
                            metadata=metadata
                        )
                    )

            logger.info(f"Search returned {len(search_results)} results")
            return search_results

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to search with query: {query[:50]}...",
                cause=e
            )

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
        if not doc_id:
            raise VectorStoreError("Document ID cannot be empty")

        try:
            # Check if document exists
            if not self.document_exists(doc_id):
                logger.warning(f"Document {doc_id} not found for deletion")
                return False

            # Delete all chunks with this doc_id
            logger.info(f"Deleting document: {doc_id}")
            self.collection.delete(
                where={"doc_id": doc_id}
            )

            logger.info(f"Successfully deleted document {doc_id}")
            return True

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete document {doc_id}",
                cause=e
            )

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
        if not doc_id:
            raise VectorStoreError("Document ID cannot be empty")

        if not chunks:
            raise VectorStoreError("Cannot update document with empty chunks list")

        try:
            # Check if document exists
            if not self.document_exists(doc_id):
                logger.warning(f"Document {doc_id} not found for update")
                return False

            # Delete old document
            logger.info(f"Updating document: {doc_id}")
            self.delete_document(doc_id)

            # Add new chunks
            self.add_document(chunks, doc_id)

            logger.info(f"Successfully updated document {doc_id}")
            return True

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to update document {doc_id}",
                cause=e
            )

    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists in the vector store.

        Args:
            doc_id: Document identifier to check

        Returns:
            True if document exists, False otherwise
        """
        if not doc_id:
            return False

        try:
            results = self.collection.get(
                where={"doc_id": doc_id},
                limit=1
            )
            return bool(results and results['ids'])
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False

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
        if not doc_id:
            raise VectorStoreError("Document ID cannot be empty")

        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if not results or not results['ids']:
                raise VectorStoreError(f"Document {doc_id} not found")

            # Reconstruct Chunk objects
            chunks = []
            for i in range(len(results['ids'])):
                chunk_id = results['ids'][i]
                document = results['documents'][i]
                metadata = results['metadatas'][i]

                chunk = Chunk(
                    text=document,
                    chunk_id=chunk_id,
                    doc_id=metadata.get('doc_id', doc_id),
                    page_number=metadata.get('page_number', 0),
                    start_pos=metadata.get('start_pos', 0),
                    end_pos=metadata.get('end_pos', 0),
                    embedding=None
                )
                chunks.append(chunk)

            logger.info(f"Retrieved {len(chunks)} chunks for document {doc_id}")
            return chunks

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                f"Failed to retrieve chunks for document {doc_id}",
                cause=e
            )

    def clear(self) -> None:
        """
        Clear all documents from the vector store.

        Raises:
            VectorStoreError: If clearing fails
        """
        try:
            logger.warning("Clearing all documents from vector store")

            # Delete the collection and recreate it
            self.client.delete_collection(self.vector_config.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.vector_config.collection_name,
                metadata={"hnsw:space": self.vector_config.distance_metric}
            )

            logger.info("Vector store cleared successfully")

        except Exception as e:
            raise VectorStoreError(
                "Failed to clear vector store",
                cause=e
            )
