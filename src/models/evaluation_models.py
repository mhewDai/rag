"""Data models for evaluation metrics."""

from dataclasses import dataclass


@dataclass
class RAGASMetrics:
    """RAGAS evaluation metrics."""

    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    overall_score: float
