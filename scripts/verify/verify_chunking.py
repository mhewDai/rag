"""Verification script for document chunking module."""

from src.chunking import DocumentChunker
from src.config.settings import ChunkConfig


def main():
    """Test the document chunking functionality."""
    print("=" * 60)
    print("Document Chunking Module Verification")
    print("=" * 60)
    
    # Test 1: Basic chunking
    print("\n1. Testing basic chunking with multiple sentences:")
    print("-" * 60)
    chunker = DocumentChunker(ChunkConfig(chunk_size=100, chunk_overlap=20))
    text = """This is the first sentence. This is the second sentence. 
    This is the third sentence. This is the fourth sentence. 
    This is the fifth sentence. This is the sixth sentence."""
    
    chunks = chunker.chunk_document(text, doc_id="test_doc_1", page_number=1)
    print(f"Input text length: {len(text)} characters")
    print(f"Number of chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Text: {chunk.text[:80]}...")
        print(f"  Length: {len(chunk.text)} characters")
        print(f"  Position: {chunk.start_pos} - {chunk.end_pos}")
        print(f"  Page: {chunk.page_number}")
    
    # Test 2: Empty text
    print("\n\n2. Testing empty text handling:")
    print("-" * 60)
    chunks = chunker.chunk_document("", doc_id="test_doc_2")
    print(f"Empty text result: {len(chunks)} chunks")
    
    # Test 3: Very short text
    print("\n\n3. Testing very short text:")
    print("-" * 60)
    short_text = "Short."
    chunks = chunker.chunk_document(short_text, doc_id="test_doc_3")
    print(f"Input: '{short_text}'")
    print(f"Number of chunks: {len(chunks)}")
    if chunks:
        print(f"Chunk text: '{chunks[0].text}'")
    
    # Test 4: Single long sentence
    print("\n\n4. Testing single long sentence:")
    print("-" * 60)
    long_sentence = "This is a very long sentence that continues on and on without any breaks or punctuation marks to split it up naturally which means the chunker will need to handle it by splitting on character boundaries instead of sentence boundaries"
    chunks = chunker.chunk_document(long_sentence, doc_id="test_doc_4")
    print(f"Input length: {len(long_sentence)} characters")
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i + 1} length: {len(chunk.text)} characters")
    
    # Test 5: Runtime config override
    print("\n\n5. Testing runtime config override:")
    print("-" * 60)
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    
    # Default config
    chunks_default = chunker.chunk_document(text, doc_id="test_doc_5a")
    print(f"With default config (chunk_size=100): {len(chunks_default)} chunks")
    
    # Override with smaller chunk size
    small_config = ChunkConfig(chunk_size=30, chunk_overlap=5)
    chunks_small = chunker.chunk_document(text, doc_id="test_doc_5b", config=small_config)
    print(f"With override config (chunk_size=30): {len(chunks_small)} chunks")
    
    # Test 6: Property document simulation
    print("\n\n6. Testing with property document-like text:")
    print("-" * 60)
    property_text = """
    Property Owner: John Smith
    Property Address: 123 Main Street, Anytown, NJ 07001
    Lot Size: 0.25 acres
    Sale Price: $450,000
    Sale Date: January 15, 2023
    Property Type: Single Family Residence
    Number of Bedrooms: 4
    Number of Bathrooms: 2.5
    Year Built: 1995
    Square Footage: 2,400 sq ft
    Tax Assessment Value: $425,000
    Annual Property Tax: $8,500
    Zoning Classification: R-1 Residential
    Parcel ID: 12-34-567-89
    """
    
    chunker_property = DocumentChunker(ChunkConfig(chunk_size=200, chunk_overlap=50))
    chunks = chunker_property.chunk_document(property_text, doc_id="property_doc_1", page_number=1)
    print(f"Property document chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}:")
        print(f"  Text preview: {chunk.text[:100]}...")
        print(f"  Length: {len(chunk.text)} characters")
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
