"""Example usage of the vector store module."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vector_store import ChromaVectorStore, VectorStoreError
from src.models.chunk_models import Chunk
from src.config.settings import VectorStoreConfig, RAGConfig


def main():
    """Demonstrate vector store functionality."""
    
    print("=" * 60)
    print("Vector Store Usage Example")
    print("=" * 60)
    
    # Initialize configuration
    vector_config = VectorStoreConfig(
        persist_directory="./data/chroma_example",
        collection_name="example_documents",
        distance_metric="cosine"
    )
    
    rag_config = RAGConfig(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        top_k_retrieval=3
    )
    
    try:
        # Initialize vector store
        print("\n1. Initializing ChromaDB vector store...")
        vector_store = ChromaVectorStore(vector_config, rag_config)
        print("   ✓ Vector store initialized")
        
        # Create sample chunks
        print("\n2. Creating sample document chunks...")
        chunks = [
            Chunk(
                text="The property is located at 123 Main Street in Springfield.",
                chunk_id="chunk_1",
                doc_id="doc_001",
                page_number=1,
                start_pos=0,
                end_pos=60
            ),
            Chunk(
                text="The lot size is 0.5 acres with a two-story colonial home.",
                chunk_id="chunk_2",
                doc_id="doc_001",
                page_number=1,
                start_pos=61,
                end_pos=120
            ),
            Chunk(
                text="Sale price was $450,000 on January 15, 2023.",
                chunk_id="chunk_3",
                doc_id="doc_001",
                page_number=1,
                start_pos=121,
                end_pos=165
            ),
            Chunk(
                text="The property has 4 bedrooms and 2.5 bathrooms.",
                chunk_id="chunk_4",
                doc_id="doc_001",
                page_number=2,
                start_pos=0,
                end_pos=47
            )
        ]
        print(f"   ✓ Created {len(chunks)} chunks")
        
        # Add document to vector store
        print("\n3. Adding document to vector store...")
        doc_id = vector_store.add_document(chunks, doc_id="doc_001")
        print(f"   ✓ Document added with ID: {doc_id}")
        
        # Check if document exists
        print("\n4. Checking if document exists...")
        exists = vector_store.document_exists("doc_001")
        print(f"   ✓ Document exists: {exists}")
        
        # Perform semantic search
        print("\n5. Performing semantic search...")
        queries = [
            "What is the address of the property?",
            "How much did the property sell for?",
            "How many bedrooms does it have?"
        ]
        
        for query in queries:
            print(f"\n   Query: '{query}'")
            results = vector_store.search(query, top_k=2)
            
            for i, result in enumerate(results, 1):
                print(f"   Result {i} (score: {result.score:.3f}):")
                print(f"     Text: {result.chunk.text}")
                print(f"     Page: {result.chunk.page_number}")
        
        # Retrieve all chunks for document
        print("\n6. Retrieving all chunks for document...")
        retrieved_chunks = vector_store.get_document_chunks("doc_001")
        print(f"   ✓ Retrieved {len(retrieved_chunks)} chunks")
        
        # Update document
        print("\n7. Updating document with new chunks...")
        new_chunks = [
            Chunk(
                text="Updated: The property is now listed at 456 Oak Avenue.",
                chunk_id="chunk_5",
                doc_id="doc_001",
                page_number=1,
                start_pos=0,
                end_pos=56
            )
        ]
        updated = vector_store.update_document("doc_001", new_chunks)
        print(f"   ✓ Document updated: {updated}")
        
        # Search after update
        print("\n8. Searching after update...")
        results = vector_store.search("What is the address?", top_k=1)
        if results:
            print(f"   Top result: {results[0].chunk.text}")
        
        # Delete document
        print("\n9. Deleting document...")
        deleted = vector_store.delete_document("doc_001")
        print(f"   ✓ Document deleted: {deleted}")
        
        # Verify deletion
        print("\n10. Verifying deletion...")
        exists_after = vector_store.document_exists("doc_001")
        print(f"   ✓ Document exists after deletion: {exists_after}")
        
        print("\n" + "=" * 60)
        print("Vector store example completed successfully!")
        print("=" * 60)
        
    except VectorStoreError as e:
        print(f"\n✗ Vector store error: {e}")
        if e.cause:
            print(f"  Caused by: {e.cause}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
