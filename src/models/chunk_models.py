"""Data models for document chunking."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Chunk:
    """A chunk of text from a document."""

    text: str
    chunk_id: str
    doc_id: str
    page_number: int
    start_pos: int
    end_pos: int
    embedding: Optional[List[float]] = None
