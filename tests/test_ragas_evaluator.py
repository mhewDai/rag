"""Unit tests for RAGAS evaluator."""

import pytest
from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.models.feature_models import ExtractionResult, FeatureValue
from src.models.evaluation_models import RAGASMetrics


class TestRAGASEvaluator:
    """Test suite for RAGASEvaluator class."""
    
    def test_evaluator_initialization(self):
        """Test that evaluator can be initialized."""
        evaluator = RAGASEvaluator()
        assert evaluator is not None
        assert evaluator.metrics is not None
        assert len(evaluator.metrics) == 4
    
    def test_evaluate_with_valid_extraction(self):
        """Test evaluation with valid extraction result."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value="John Smith",
                    confidence=0.95,
                    source_chunks=["Owner: John Smith"],
                    source_pages=[1],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        metrics = evaluator.evaluate(extraction_result)
        
        assert isinstance(metrics, RAGASMetrics)
        assert 0.0 <= metrics.faithfulness <= 1.0
        assert 0.0 <= metrics.answer_relevance <= 1.0
        assert 0.0 <= metrics.context_precision <= 1.0
        assert 0.0 <= metrics.context_recall <= 1.0
        assert 0.0 <= metrics.overall_score <= 1.0
    
    def test_evaluate_with_empty_extraction(self):
        """Test evaluation with empty extraction result."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="empty_doc",
            features={},
            processing_time=0.1,
            metadata={},
        )
        
        metrics = evaluator.evaluate(extraction_result)
        
        assert metrics.faithfulness == 0.0
        assert metrics.answer_relevance == 0.0
        assert metrics.context_precision == 0.0
        assert metrics.context_recall == 0.0
        assert metrics.overall_score == 0.0
    
    def test_evaluate_with_null_values(self):
        """Test evaluation with null feature values."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="null_doc",
            features={
                "owner_name": FeatureValue(
                    value=None,
                    confidence=0.0,
                    source_chunks=[],
                    source_pages=[],
                ),
                "sale_price": FeatureValue(
                    value="$500,000",
                    confidence=0.90,
                    source_chunks=["Sale price: $500,000"],
                    source_pages=[1],
                ),
            },
            processing_time=2.0,
            metadata={},
        )
        
        metrics = evaluator.evaluate(extraction_result)
        
        # Should only evaluate non-null features
        assert isinstance(metrics, RAGASMetrics)
        assert 0.0 <= metrics.overall_score <= 1.0
    
    def test_evaluate_with_ground_truth(self):
        """Test evaluation with ground truth data."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value="John Smith",
                    confidence=0.95,
                    source_chunks=["Owner: John Smith"],
                    source_pages=[1],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        ground_truth = {
            "owner_name": "John Smith",
        }
        
        metrics = evaluator.evaluate(extraction_result, ground_truth)
        
        assert isinstance(metrics, RAGASMetrics)
        assert 0.0 <= metrics.overall_score <= 1.0
    
    def test_compute_faithfulness(self):
        """Test faithfulness computation."""
        evaluator = RAGASEvaluator()
        
        answer = "John Smith"
        context = ["Owner: John Smith", "Property owned by John Smith"]
        
        score = evaluator.compute_faithfulness(answer, context)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_compute_answer_relevance(self):
        """Test answer relevance computation."""
        evaluator = RAGASEvaluator()
        
        question = "Who is the owner?"
        answer = "John Smith"
        
        score = evaluator.compute_answer_relevance(question, answer)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_compute_context_precision(self):
        """Test context precision computation."""
        evaluator = RAGASEvaluator()
        
        question = "What is the sale price?"
        contexts = ["Sale price: $500,000"]
        ground_truth = "$500,000"
        
        score = evaluator.compute_context_precision(question, contexts, ground_truth)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_compute_context_precision_without_ground_truth(self):
        """Test context precision returns 0 without ground truth."""
        evaluator = RAGASEvaluator()
        
        question = "What is the sale price?"
        contexts = ["Sale price: $500,000"]
        
        score = evaluator.compute_context_precision(question, contexts, None)
        
        assert score == 0.0
    
    def test_compute_context_recall(self):
        """Test context recall computation."""
        evaluator = RAGASEvaluator()
        
        contexts = ["Sale price: $500,000"]
        ground_truth = "$500,000"
        
        score = evaluator.compute_context_recall(contexts, ground_truth)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_prepare_dataset(self):
        """Test dataset preparation for RAGAS."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value="John Smith",
                    confidence=0.95,
                    source_chunks=["Owner: John Smith"],
                    source_pages=[1],
                ),
                "sale_price": FeatureValue(
                    value="$500,000",
                    confidence=0.90,
                    source_chunks=["Sale price: $500,000"],
                    source_pages=[2],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        dataset = evaluator._prepare_dataset(extraction_result)
        
        assert "question" in dataset
        assert "answer" in dataset
        assert "contexts" in dataset
        assert "ground_truth" in dataset
        assert len(dataset["question"]) == 2
        assert len(dataset["answer"]) == 2
        assert len(dataset["contexts"]) == 2
        assert len(dataset["ground_truth"]) == 2
    
    def test_prepare_dataset_skips_null_values(self):
        """Test that dataset preparation skips null values."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value=None,
                    confidence=0.0,
                    source_chunks=[],
                    source_pages=[],
                ),
                "sale_price": FeatureValue(
                    value="$500,000",
                    confidence=0.90,
                    source_chunks=["Sale price: $500,000"],
                    source_pages=[2],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        dataset = evaluator._prepare_dataset(extraction_result)
        
        # Should only include non-null features
        assert len(dataset["question"]) == 1
        assert len(dataset["answer"]) == 1
    
    def test_prepare_dataset_with_ground_truth(self):
        """Test dataset preparation with ground truth."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value="John Smith",
                    confidence=0.95,
                    source_chunks=["Owner: John Smith"],
                    source_pages=[1],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        ground_truth = {
            "owner_name": "John Smith",
        }
        
        dataset = evaluator._prepare_dataset(extraction_result, ground_truth)
        
        assert dataset["ground_truth"][0] == "John Smith"
    
    def test_prepare_dataset_handles_missing_contexts(self):
        """Test that dataset preparation handles missing contexts."""
        evaluator = RAGASEvaluator()
        
        extraction_result = ExtractionResult(
            doc_id="test_doc",
            features={
                "owner_name": FeatureValue(
                    value="John Smith",
                    confidence=0.95,
                    source_chunks=[],  # Empty contexts
                    source_pages=[],
                ),
            },
            processing_time=1.0,
            metadata={},
        )
        
        dataset = evaluator._prepare_dataset(extraction_result)
        
        # Should provide default context
        assert len(dataset["contexts"][0]) > 0
        assert dataset["contexts"][0][0] == "No context available"
