"""Verification script for RAG extraction engine."""

import os
from src.rag.extraction_engine import RAGExtractionEngine
from src.models.property_features import create_property_feature_schema
from src.vector_store.chroma_store import ChromaVectorStore
from src.config.settings import RAGConfig, VectorStoreConfig
from src.models.chunk_models import Chunk

def main():
    """Verify RAG extraction engine implementation."""
    print("=" * 60)
    print("RAG Extraction Engine Verification")
    print("=" * 60)
    
    # Check if API keys are available
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("\n⚠️  Warning: No API keys found in environment")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test LLM integration")
        print("\nTesting basic initialization only...\n")
    
    # Create configurations
    rag_config = RAGConfig(
        llm_model="gpt-4",
        llm_temperature=0.0,
        top_k_retrieval=3,
        confidence_threshold=0.5,
    )
    
    vector_config = VectorStoreConfig(
        persist_directory="./data/test_chroma",
        collection_name="test_rag_verification",
    )
    
    # Initialize vector store
    print("1. Initializing vector store...")
    vector_store = ChromaVectorStore(vector_config)
    print("   ✓ Vector store initialized")
    
    # Initialize RAG engine
    print("\n2. Initializing RAG extraction engine...")
    try:
        engine = RAGExtractionEngine(
            vector_store=vector_store,
            config=rag_config,
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
        )
        print("   ✓ RAG engine initialized")
    except ValueError as e:
        print(f"   ✗ Failed to initialize: {e}")
        return
    
    # Test feature schema loading
    print("\n3. Loading property feature schema...")
    feature_schema = create_property_feature_schema()
    print(f"   ✓ Loaded {len(feature_schema)} feature definitions")
    
    # Test query generation
    print("\n4. Testing query generation...")
    test_feature = feature_schema["owner_name"]
    query = engine._generate_query(test_feature)
    print(f"   ✓ Generated query: '{query[:60]}...'")
    
    # Test with mock document (if we have API keys)
    if openai_key or anthropic_key:
        print("\n5. Testing with mock document...")
        
        # Add a test document to vector store
        test_chunks = [
            Chunk(
                text="Property Owner: John Smith. The property is located at 123 Main Street.",
                chunk_id="chunk_1",
                doc_id="test_doc_1",
                page_number=1,
                start_pos=0,
                end_pos=72,
            ),
            Chunk(
                text="Sale Price: $450,000. Sale Date: 03/15/2023. The property was sold to John Smith.",
                chunk_id="chunk_2",
                doc_id="test_doc_1",
                page_number=1,
                start_pos=73,
                end_pos=155,
            ),
        ]
        
        doc_id = vector_store.add_document(test_chunks, doc_id="test_doc_1")
        print(f"   ✓ Added test document: {doc_id}")
        
        # Test single feature extraction
        print("\n6. Testing single feature extraction...")
        try:
            feature_value = engine.extract_single_feature(
                doc_id="test_doc_1",
                feature=test_feature,
            )
            print(f"   ✓ Extracted value: {feature_value.value}")
            print(f"   ✓ Confidence: {feature_value.confidence:.2f}")
            print(f"   ✓ Source pages: {feature_value.source_pages}")
            print(f"   ✓ Source chunks: {len(feature_value.source_chunks)}")
        except Exception as e:
            print(f"   ✗ Extraction failed: {e}")
        
        # Test full extraction
        print("\n7. Testing full feature extraction...")
        try:
            # Use a subset of features for testing
            test_schema = {
                "owner_name": feature_schema["owner_name"],
                "sale_price": feature_schema["sale_price"],
                "property_address": feature_schema["property_address"],
            }
            
            result = engine.extract_features(
                doc_id="test_doc_1",
                feature_schema=test_schema,
            )
            
            print(f"   ✓ Extracted {len(result.features)} features")
            print(f"   ✓ Processing time: {result.processing_time:.2f}s")
            
            for name, value in result.features.items():
                status = "✓" if value.value is not None else "○"
                print(f"   {status} {name}: {value.value} (confidence: {value.confidence:.2f})")
        
        except Exception as e:
            print(f"   ✗ Full extraction failed: {e}")
        
        # Cleanup
        vector_store.delete_document("test_doc_1")
        print("\n   ✓ Cleaned up test document")
    
    else:
        print("\n5-7. Skipping LLM tests (no API keys)")
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    
    # Cleanup vector store
    try:
        vector_store.clear()
    except:
        pass

if __name__ == "__main__":
    main()
