"""Data models for pipeline orchestration."""

from dataclasses import dataclass
from typing import List, Dict, Any
from .feature_models import ExtractionResult
from .evaluation_models import RAGASMetrics
from .error_models import ErrorInfo


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
