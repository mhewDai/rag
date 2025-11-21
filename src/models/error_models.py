"""Data models for error handling."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ErrorInfo:
    """Information about an error that occurred during processing."""

    error_code: str
    error_message: str
    component: str
    doc_id: Optional[str]
    timestamp: datetime
    stack_trace: Optional[str]
    retry_count: int
