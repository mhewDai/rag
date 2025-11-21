"""Verification script for vector store implementation."""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.vector_store import ChromaVectorStore, VectorStoreError
from src.models.chunk_models import Chunk
from src.config.settings import VectorStoreConfig, RAGConfig


def test_vector_store_basic_operations():
    """Test basic vector store operations."""
    print("Testing basic vector store operations...")
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize configuration
        vector_config = VectorStoreConfig(
            persist_directory=temp_dir,
            collection_name="test_collection",
            distance_metric="cosine"
        )
        
        rag_config = RAGConfig(
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize vector store
        vector_store = ChromaVectorStore(vector_config, rag_config)
        print("✓ Vector store initialized")
        
        # Create test chunks
        chunks = [
            Chunk(
                text="The property is located at 123 Main Street.",
                chunk_id="chunk_1",
                doc_id="doc_001",
                page_number=1,
                start_pos=0,
                end_pos=44
            ),
            Chunk(
                text="Sale price was $450,000.",
                chunk_id="chunk_2",
                doc_id="doc_001",
                page_number=1,
                start_pos=45,
                end_pos=69
            )
        ]
        
        # Test add_document
        doc_id = vector_store.add_document(chunks, doc_id="doc_001")
        assert doc_id == "doc_001", "Document ID mismatch"
        print("✓ add_document works")
        
        # Test document_exists
        exists = vector_store.document_exists("doc_001")
        assert exists, "Document should exist"
        print("✓ document_exists works")
        
        # Test search
        results = vector_store.search("What is the address?", top_k=1)
        assert len(results) > 0, "Search should return results"
        assert "Main Street" in results[0].chunk.text, "Search should find relevant chunk"
        print("✓ search works")
        
        # Test get_document_chunks
        retrieved_chunks = vector_store.get_document_chunks("doc_001")
        assert len(retrieved_chunks) == 2, "Should retrieve all chunks"
        print("✓ get_document_chunks works")
        
        # Test update_document
        new_chunks = [
            Chunk(
                text="Updated property at 456 Oak Avenue.",
                chunk_id="chunk_3",
                doc_id="doc_001",
                page_number=1,
                start_pos=0,
                end_pos=36
            )
        ]
        updated = vector_store.update_document("doc_001", new_chunks)
        assert updated, "Update should succeed"
        
        updated_chunks = vector_store.get_document_chunks("doc_001")
        assert len(updated_chunks) == 1, "Should have only new chunks"
        print("✓ update_document works")
        
        # Test delete_document
        deleted = vector_store.delete_document("doc_001")
        assert deleted, "Delete should succeed"
        
        exists_after = vector_store.document_exists("doc_001")
        assert not exists_after, "Document should not exist after deletion"
        print("✓ delete_document works")
        
        # Test clear
        vector_store.add_document(chunks, doc_id="doc_002")
        vector_store.clear()
        exists_after_clear = vector_store.document_exists("doc_002")
        assert not exists_after_clear, "Document should not exist after clear"
        print("✓ clear works")
        
        print("\n✅ All vector store tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)



def test_vector_store_error_handling():
    """Test error handling in vector store."""
    print("\nTesting error handling...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        vector_config = VectorStoreConfig(
            persist_directory=temp_dir,
            collection_name="test_collection"
        )
        
        rag_config = RAGConfig()
        
        vector_store = ChromaVectorStore(vector_config, rag_config)
        
        # Test empty chunks
        try:
            vector_store.add_document([])
            print("❌ Should raise error for empty chunks")
            return False
        except VectorStoreError:
            print("✓ Correctly raises error for empty chunks")
        
        # Test empty query
        try:
            vector_store.search("")
            print("❌ Should raise error for empty query")
            return False
        except VectorStoreError:
            print("✓ Correctly raises error for empty query")
        
        # Test invalid top_k
        try:
            vector_store.search("test", top_k=0)
            print("❌ Should raise error for invalid top_k")
            return False
        except VectorStoreError:
            print("✓ Correctly raises error for invalid top_k")
        
        # Test delete non-existent document
        deleted = vector_store.delete_document("non_existent")
        assert not deleted, "Should return False for non-existent document"
        print("✓ Correctly handles non-existent document deletion")
        
        # Test get chunks for non-existent document
        try:
            vector_store.get_document_chunks("non_existent")
            print("❌ Should raise error for non-existent document")
            return False
        except VectorStoreError:
            print("✓ Correctly raises error for non-existent document")
        
        print("\n✅ All error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Vector Store Implementation Verification")
    print("=" * 60)
    print()
    
    success = True
    
    # Run basic operations test
    if not test_vector_store_basic_operations():
        success = False
    
    # Run error handling test
    if not test_vector_store_error_handling():
        success = False
    
    print()
    print("=" * 60)
    if success:
        print("✅ All verification tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
