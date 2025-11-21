"""Verification script for RAGAS evaluator implementation."""

import os
from dotenv import load_dotenv

from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.models.feature_models import ExtractionResult, FeatureValue
from src.models.evaluation_models import RAGASMetrics

# Load environment variables
load_dotenv()


def test_ragas_evaluator_basic():
    """Test basic RAGAS evaluator functionality."""
    print("Testing RAGAS Evaluator...")
    
    # Create evaluator
    evaluator = RAGASEvaluator()
    
    # Create sample extraction result
    extraction_result = ExtractionResult(
        doc_id="test_doc_1",
        features={
            "owner_name": FeatureValue(
                value="John Smith",
                confidence=0.95,
                source_chunks=[
                    "The property is owned by John Smith.",
                    "Owner: John Smith, 123 Main St",
                ],
                source_pages=[1],
            ),
            "sale_price": FeatureValue(
                value="$500,000",
                confidence=0.90,
                source_chunks=[
                    "Sale price: $500,000",
                    "The property was sold for five hundred thousand dollars.",
                ],
                source_pages=[2],
            ),
            "lot_size": FeatureValue(
                value="0.5 acres",
                confidence=0.85,
                source_chunks=[
                    "Lot size: 0.5 acres",
                ],
                source_pages=[1],
            ),
        },
        processing_time=5.2,
        metadata={"model": "gpt-4"},
    )
    
    # Test evaluation without ground truth
    print("\n1. Testing evaluation without ground truth...")
    metrics = evaluator.evaluate(extraction_result)
    
    print(f"   Faithfulness: {metrics.faithfulness:.3f}")
    print(f"   Answer Relevance: {metrics.answer_relevance:.3f}")
    print(f"   Context Precision: {metrics.context_precision:.3f}")
    print(f"   Context Recall: {metrics.context_recall:.3f}")
    print(f"   Overall Score: {metrics.overall_score:.3f}")
    
    assert isinstance(metrics, RAGASMetrics)
    assert 0.0 <= metrics.faithfulness <= 1.0
    assert 0.0 <= metrics.answer_relevance <= 1.0
    assert 0.0 <= metrics.context_precision <= 1.0
    assert 0.0 <= metrics.context_recall <= 1.0
    assert 0.0 <= metrics.overall_score <= 1.0
    print("   ✓ Metrics computed successfully")
    
    # Test evaluation with ground truth
    print("\n2. Testing evaluation with ground truth...")
    ground_truth = {
        "owner_name": "John Smith",
        "sale_price": "$500,000",
        "lot_size": "0.5 acres",
    }
    
    metrics_with_gt = evaluator.evaluate(extraction_result, ground_truth)
    
    print(f"   Faithfulness: {metrics_with_gt.faithfulness:.3f}")
    print(f"   Answer Relevance: {metrics_with_gt.answer_relevance:.3f}")
    print(f"   Context Precision: {metrics_with_gt.context_precision:.3f}")
    print(f"   Context Recall: {metrics_with_gt.context_recall:.3f}")
    print(f"   Overall Score: {metrics_with_gt.overall_score:.3f}")
    
    assert isinstance(metrics_with_gt, RAGASMetrics)
    print("   ✓ Metrics with ground truth computed successfully")
    
    # Test empty extraction result
    print("\n3. Testing empty extraction result...")
    empty_result = ExtractionResult(
        doc_id="empty_doc",
        features={},
        processing_time=0.1,
        metadata={},
    )
    
    empty_metrics = evaluator.evaluate(empty_result)
    
    assert empty_metrics.faithfulness == 0.0
    assert empty_metrics.answer_relevance == 0.0
    assert empty_metrics.context_precision == 0.0
    assert empty_metrics.context_recall == 0.0
    assert empty_metrics.overall_score == 0.0
    print("   ✓ Empty result handled correctly")
    
    # Test extraction with null values
    print("\n4. Testing extraction with null values...")
    null_result = ExtractionResult(
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
    
    null_metrics = evaluator.evaluate(null_result)
    
    assert isinstance(null_metrics, RAGASMetrics)
    print("   ✓ Null values handled correctly")
    
    print("\n✅ All RAGAS evaluator tests passed!")


def test_individual_metrics():
    """Test individual metric computation methods."""
    print("\nTesting Individual Metrics...")
    
    evaluator = RAGASEvaluator()
    
    # Test faithfulness
    print("\n1. Testing faithfulness computation...")
    answer = "The property is owned by John Smith"
    context = [
        "Owner: John Smith",
        "The property at 123 Main St is owned by John Smith",
    ]
    
    faithfulness_score = evaluator.compute_faithfulness(answer, context)
    print(f"   Faithfulness score: {faithfulness_score:.3f}")
    assert 0.0 <= faithfulness_score <= 1.0
    print("   ✓ Faithfulness computed")
    
    # Test answer relevance
    print("\n2. Testing answer relevance computation...")
    question = "Who is the owner of the property?"
    answer = "John Smith"
    
    relevance_score = evaluator.compute_answer_relevance(question, answer)
    print(f"   Answer relevance score: {relevance_score:.3f}")
    assert 0.0 <= relevance_score <= 1.0
    print("   ✓ Answer relevance computed")
    
    # Test context precision (requires ground truth)
    print("\n3. Testing context precision computation...")
    question = "What is the sale price?"
    contexts = [
        "Sale price: $500,000",
        "The property was sold in 2023",
    ]
    ground_truth = "$500,000"
    
    precision_score = evaluator.compute_context_precision(
        question, contexts, ground_truth
    )
    print(f"   Context precision score: {precision_score:.3f}")
    assert 0.0 <= precision_score <= 1.0
    print("   ✓ Context precision computed")
    
    # Test context recall
    print("\n4. Testing context recall computation...")
    contexts = [
        "Sale price: $500,000",
        "Sold on January 15, 2023",
    ]
    ground_truth = "$500,000"
    
    recall_score = evaluator.compute_context_recall(contexts, ground_truth)
    print(f"   Context recall score: {recall_score:.3f}")
    assert 0.0 <= recall_score <= 1.0
    print("   ✓ Context recall computed")
    
    print("\n✅ All individual metric tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("RAGAS Evaluator Verification")
    print("=" * 60)
    
    try:
        test_ragas_evaluator_basic()
        test_individual_metrics()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
