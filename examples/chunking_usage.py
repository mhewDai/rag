"""Example usage of the document chunking module."""

from src.chunking import DocumentChunker
from src.config.settings import ChunkConfig


def example_basic_chunking():
    """Example: Basic document chunking."""
    print("Example 1: Basic Document Chunking")
    print("-" * 60)
    
    # Create a chunker with default configuration
    chunker = DocumentChunker()
    
    # Sample text
    text = """
    The property is located at 123 Main Street in Anytown, New Jersey.
    The lot size is approximately 0.25 acres with a single-family home.
    The property was sold on January 15, 2023 for $450,000.
    The home features 4 bedrooms and 2.5 bathrooms.
    It was built in 1995 and has 2,400 square feet of living space.
    """
    
    # Chunk the document
    chunks = chunker.chunk_document(text, doc_id="property_001", page_number=1)
    
    print(f"Created {len(chunks)} chunks from the document\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Text: {chunk.text}")
        print(f"  Position: {chunk.start_pos}-{chunk.end_pos}")
        print()


def example_custom_config():
    """Example: Chunking with custom configuration."""
    print("\nExample 2: Custom Configuration")
    print("-" * 60)
    
    # Create custom configuration
    config = ChunkConfig(
        chunk_size=150,      # Smaller chunks
        chunk_overlap=30,    # More overlap
        min_chunk_size=20
    )
    
    chunker = DocumentChunker(config)
    
    text = """
    Property Owner: Jane Doe. Property Address: 456 Oak Avenue, Springfield, NJ 07081.
    Lot Size: 0.5 acres. Sale Price: $575,000. Sale Date: March 10, 2023.
    Property Type: Colonial. Bedrooms: 5. Bathrooms: 3. Year Built: 2005.
    Square Footage: 3,200 sq ft. Tax Assessment: $550,000. Annual Tax: $11,000.
    """
    
    chunks = chunker.chunk_document(text, doc_id="property_002")
    
    print(f"Created {len(chunks)} chunks with custom config")
    print(f"Config: chunk_size={config.chunk_size}, overlap={config.chunk_overlap}\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {len(chunk.text)} characters")
        print(f"  {chunk.text[:80]}...")
        print()


def example_runtime_override():
    """Example: Runtime configuration override."""
    print("\nExample 3: Runtime Configuration Override")
    print("-" * 60)
    
    # Create chunker with default config
    chunker = DocumentChunker(ChunkConfig(chunk_size=200, chunk_overlap=40))
    
    text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
    
    # Use default config
    chunks_default = chunker.chunk_document(text, doc_id="doc_a")
    print(f"Default config: {len(chunks_default)} chunks")
    
    # Override at runtime
    override_config = ChunkConfig(chunk_size=50, chunk_overlap=10)
    chunks_override = chunker.chunk_document(text, doc_id="doc_b", config=override_config)
    print(f"Override config: {len(chunks_override)} chunks")


def example_multi_page_document():
    """Example: Processing multi-page document."""
    print("\nExample 4: Multi-Page Document")
    print("-" * 60)
    
    chunker = DocumentChunker()
    
    # Simulate pages from a multi-page document
    pages = [
        ("Page 1 content: Property details and owner information.", 1),
        ("Page 2 content: Sale history and transaction records.", 2),
        ("Page 3 content: Tax assessment and zoning information.", 3),
    ]
    
    all_chunks = []
    for page_text, page_num in pages:
        chunks = chunker.chunk_document(
            page_text, 
            doc_id="multi_page_doc", 
            page_number=page_num
        )
        all_chunks.extend(chunks)
        print(f"Page {page_num}: {len(chunks)} chunks")
    
    print(f"\nTotal chunks across all pages: {len(all_chunks)}")


def example_edge_cases():
    """Example: Handling edge cases."""
    print("\nExample 5: Edge Cases")
    print("-" * 60)
    
    chunker = DocumentChunker()
    
    # Empty text
    chunks = chunker.chunk_document("", doc_id="empty_doc")
    print(f"Empty text: {len(chunks)} chunks")
    
    # Very short text
    chunks = chunker.chunk_document("Short.", doc_id="short_doc")
    print(f"Very short text: {len(chunks)} chunks")
    
    # Single long sentence without punctuation
    long_text = "This is a very long sentence without proper punctuation that goes on and on"
    chunks = chunker.chunk_document(long_text, doc_id="long_doc")
    print(f"Long single sentence: {len(chunks)} chunks")
    
    # Whitespace only
    chunks = chunker.chunk_document("   \n\t  ", doc_id="whitespace_doc")
    print(f"Whitespace only: {len(chunks)} chunks")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Document Chunking Module - Usage Examples")
    print("=" * 60)
    
    example_basic_chunking()
    example_custom_config()
    example_runtime_override()
    example_multi_page_document()
    example_edge_cases()
    
    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
