"""Document chunking module for text segmentation."""

import re
import uuid
from typing import List, Optional

from src.config.settings import ChunkConfig
from src.models.chunk_models import Chunk


class DocumentChunker:
    """
    Chunks documents into overlapping segments with sentence-aware splitting.

    This class implements a sliding window approach that respects sentence
    boundaries to create semantically meaningful chunks for retrieval.
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Initialize the document chunker.

        Args:
            config: Chunking configuration. If None, uses defaults.
        """
        self.config = config or ChunkConfig()

    def chunk_document(
        self,
        text: str,
        doc_id: str,
        page_number: int = 1,
        config: Optional[ChunkConfig] = None
    ) -> List[Chunk]:
        """
        Split document into overlapping chunks with sentence-aware splitting.

        Args:
            text: Extracted text from OCR or other source
            doc_id: Document identifier
            page_number: Page number for metadata (default: 1)
            config: Optional runtime configuration override

        Returns:
            List of Chunk objects with text, metadata, and position info
        """
        # Use runtime config if provided, otherwise use instance config
        chunk_config = config or self.config

        # Handle empty or very short documents
        if not text or not text.strip():
            return []

        text = text.strip()

        # Handle very short documents (shorter than min_chunk_size)
        if len(text) < chunk_config.min_chunk_size:
            return [
                Chunk(
                    text=text,
                    chunk_id=self._generate_chunk_id(doc_id, 0),
                    doc_id=doc_id,
                    page_number=page_number,
                    start_pos=0,
                    end_pos=len(text),
                    embedding=None
                )
            ]

        # Split text into sentences
        sentences = self._split_into_sentences(text)

        # Handle single sentence documents
        if len(sentences) == 1:
            sentence = sentences[0]
            # If single sentence is too long, split by character
            if len(sentence) > chunk_config.chunk_size:
                return self._chunk_by_character(
                    sentence, doc_id, page_number, chunk_config
                )
            else:
                return [
                    Chunk(
                        text=sentence,
                        chunk_id=self._generate_chunk_id(doc_id, 0),
                        doc_id=doc_id,
                        page_number=page_number,
                        start_pos=0,
                        end_pos=len(sentence),
                        embedding=None
                    )
                ]

        # Build chunks using sliding window with sentence awareness
        chunks = []
        current_chunk_sentences = []
        current_chunk_length = 0
        sentence_start_positions = self._get_sentence_positions(text, sentences)

        i = 0
        chunk_index = 0

        while i < len(sentences):
            sentence = sentences[i]
            sentence_length = len(sentence)

            # Check if adding this sentence would exceed chunk_size
            would_exceed = current_chunk_length + sentence_length > chunk_config.chunk_size
            if would_exceed and current_chunk_sentences:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk_sentences)
                start_pos = sentence_start_positions[i - len(current_chunk_sentences)]
                end_pos = start_pos + len(chunk_text)

                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_id=self._generate_chunk_id(doc_id, chunk_index),
                        doc_id=doc_id,
                        page_number=page_number,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        embedding=None
                    )
                )
                chunk_index += 1

                # Calculate overlap: keep sentences that fit within overlap size
                overlap_length = 0
                overlap_sentences = []
                for sent in reversed(current_chunk_sentences):
                    if overlap_length + len(sent) <= chunk_config.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_length += len(sent) + 1  # +1 for space
                    else:
                        break

                current_chunk_sentences = overlap_sentences
                current_chunk_length = overlap_length
            else:
                # Add sentence to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_length += sentence_length + 1  # +1 for space
                i += 1

        # Add final chunk if there are remaining sentences
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            start_pos = sentence_start_positions[len(sentences) - len(current_chunk_sentences)]
            end_pos = start_pos + len(chunk_text)

            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_id=self._generate_chunk_id(doc_id, chunk_index),
                    doc_id=doc_id,
                    page_number=page_number,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    embedding=None
                )
            )

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.

        This handles common sentence boundaries while avoiding false positives
        like abbreviations and decimal numbers.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Pattern matches sentence endings: . ! ? followed by space and capital letter
        # or end of string
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'

        # Split by sentence boundaries
        sentences = re.split(sentence_pattern, text)

        # Clean up sentences: strip whitespace and filter empty
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _get_sentence_positions(self, text: str, sentences: List[str]) -> List[int]:
        """
        Get the starting position of each sentence in the original text.

        Args:
            text: Original text
            sentences: List of sentences

        Returns:
            List of starting positions for each sentence
        """
        positions = []
        search_start = 0

        for sentence in sentences:
            # Find the sentence in the text starting from search_start
            pos = text.find(sentence, search_start)
            if pos == -1:
                # Fallback: use search_start if exact match not found
                pos = search_start
            positions.append(pos)
            search_start = pos + len(sentence)

        return positions

    def _chunk_by_character(
        self,
        text: str,
        doc_id: str,
        page_number: int,
        config: ChunkConfig
    ) -> List[Chunk]:
        """
        Chunk text by character count when sentence-based chunking isn't suitable.

        This is used for very long single sentences or when sentence splitting fails.

        Args:
            text: Text to chunk
            doc_id: Document identifier
            page_number: Page number
            config: Chunking configuration

        Returns:
            List of character-based chunks
        """
        chunks = []
        chunk_index = 0
        start = 0

        while start < len(text):
            end = min(start + config.chunk_size, len(text))
            chunk_text = text[start:end]

            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_id=self._generate_chunk_id(doc_id, chunk_index),
                    doc_id=doc_id,
                    page_number=page_number,
                    start_pos=start,
                    end_pos=end,
                    embedding=None
                )
            )

            chunk_index += 1
            # Move start forward by (chunk_size - overlap)
            start += config.chunk_size - config.chunk_overlap

        return chunks

    def _generate_chunk_id(self, doc_id: str, chunk_index: int) -> str:
        """
        Generate a unique chunk identifier.

        Args:
            doc_id: Document identifier
            chunk_index: Index of chunk within document

        Returns:
            Unique chunk ID
        """
        return f"{doc_id}_chunk_{chunk_index}_{uuid.uuid4().hex[:8]}"
