"""Data models for pipeline orchestration."""

from dataclasses import dataclass
from typing import Any, Dict, List

from .error_models import ErrorInfo
from .evaluation_models import RAGASMetrics
from .feature_models import ExtractionResult


@dataclass
class PipelineResult:
    """Result of processing a single document through the pipeline."""

    doc_id: str
    extraction: ExtractionResult
    ragas_metrics: RAGASMetrics
    errors: List[ErrorInfo]
    success: bool


@dataclass
class BatchResult:
    """Result of processing a batch of documents."""

    results: List[PipelineResult]
    total_documents: int
    successful_documents: int
    failed_documents: int
    processing_time: float
    metadata: Dict[str, Any]
