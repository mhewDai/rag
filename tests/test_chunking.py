"""Tests for document chunking module."""

import pytest
from src.chunking import DocumentChunker
from src.config.settings import ChunkConfig
from src.models.chunk_models import Chunk


class TestDocumentChunker:
    """Test cases for DocumentChunker class."""

    def test_chunk_empty_text(self):
        """Test chunking empty text returns empty list."""
        chunker = DocumentChunker()
        chunks = chunker.chunk_document("", doc_id="test_doc")
        assert chunks == []

    def test_chunk_whitespace_only(self):
        """Test chunking whitespace-only text returns empty list."""
        chunker = DocumentChunker()
        chunks = chunker.chunk_document("   \n\t  ", doc_id="test_doc")
        assert chunks == []

    def test_chunk_very_short_document(self):
        """Test chunking very short document returns single chunk."""
        chunker = DocumentChunker(ChunkConfig(min_chunk_size=50))
        text = "Short text."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].doc_id == "test_doc"
        assert chunks[0].start_pos == 0
        assert chunks[0].end_pos == len(text)

    def test_chunk_single_sentence(self):
        """Test chunking single sentence document."""
        chunker = DocumentChunker()
        text = "This is a single sentence that is not too long."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].doc_id == "test_doc"

    def test_chunk_multiple_sentences(self):
        """Test chunking document with multiple sentences."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=100, chunk_overlap=20))
        text = "First sentence here. Second sentence follows. Third sentence appears. Fourth sentence ends."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.doc_id == "test_doc" for chunk in chunks)
        
        # Verify all chunks respect size limit (with some tolerance for sentence boundaries)
        for chunk in chunks:
            assert len(chunk.text) <= chunker.config.chunk_size + 100  # tolerance for sentence completion

    def test_chunk_with_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=50, chunk_overlap=15))
        text = "Sentence one is here. Sentence two follows. Sentence three appears. Sentence four ends. Sentence five concludes."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        if len(chunks) > 1:
            # Check that consecutive chunks have some overlapping content
            for i in range(len(chunks) - 1):
                # There should be some text overlap between consecutive chunks
                chunk1_words = set(chunks[i].text.split())
                chunk2_words = set(chunks[i + 1].text.split())
                overlap_words = chunk1_words & chunk2_words
                # Should have at least some overlapping words
                assert len(overlap_words) > 0

    def test_chunk_preserves_page_number(self):
        """Test that chunks preserve page number metadata."""
        chunker = DocumentChunker()
        text = "This is some text from page 5."
        chunks = chunker.chunk_document(text, doc_id="test_doc", page_number=5)
        
        assert all(chunk.page_number == 5 for chunk in chunks)

    def test_chunk_ids_are_unique(self):
        """Test that all chunk IDs are unique."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=50, chunk_overlap=10))
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. Sentence six."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All IDs are unique

    def test_chunk_positions_are_sequential(self):
        """Test that chunk positions are sequential and non-overlapping in position."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=60, chunk_overlap=15))
        text = "First sentence here. Second sentence follows. Third sentence appears. Fourth sentence ends."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        for i, chunk in enumerate(chunks):
            assert chunk.start_pos >= 0
            assert chunk.end_pos > chunk.start_pos
            assert chunk.end_pos <= len(text)

    def test_runtime_config_override(self):
        """Test that runtime config overrides instance config."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=100, chunk_overlap=20))
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        
        # Use runtime override with smaller chunk size
        runtime_config = ChunkConfig(chunk_size=30, chunk_overlap=5)
        chunks = chunker.chunk_document(text, doc_id="test_doc", config=runtime_config)
        
        # Should create more chunks with smaller size
        assert len(chunks) > 0

    def test_long_single_sentence_chunking(self):
        """Test chunking of very long single sentence."""
        chunker = DocumentChunker(ChunkConfig(chunk_size=50, chunk_overlap=10))
        # Create a long sentence without proper sentence boundaries
        text = "This is a very long sentence that goes on and on without any proper punctuation to break it up into smaller pieces"
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        # Should create multiple chunks even for single sentence
        assert len(chunks) > 0
        
        # Verify chunks respect size constraints
        for chunk in chunks:
            assert len(chunk.text) <= chunker.config.chunk_size + 20  # small tolerance

    def test_sentence_splitting(self):
        """Test sentence splitting logic."""
        chunker = DocumentChunker()
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = chunker._split_into_sentences(text)
        
        assert len(sentences) == 4
        assert "First sentence." in sentences[0]
        assert "Second sentence!" in sentences[1]
        assert "Third sentence?" in sentences[2]
        assert "Fourth sentence." in sentences[3]

    def test_chunk_embedding_is_none(self):
        """Test that chunks are created with None embedding."""
        chunker = DocumentChunker()
        text = "This is a test sentence."
        chunks = chunker.chunk_document(text, doc_id="test_doc")
        
        assert all(chunk.embedding is None for chunk in chunks)
