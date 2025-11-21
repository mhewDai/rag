"""Example usage of RAGAS evaluator for RAG system quality assessment."""

import os
from dotenv import load_dotenv

from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.models.feature_models import ExtractionResult, FeatureValue

# Load environment variables
load_dotenv()


def main():
    """Demonstrate RAGAS evaluator usage."""
    print("RAGAS Evaluator Example")
    print("=" * 60)
    
    # Initialize evaluator
    print("\n1. Initializing RAGAS evaluator...")
    evaluator = RAGASEvaluator()
    print("   ✓ Evaluator initialized")
    
    # Create sample extraction result
    print("\n2. Creating sample extraction result...")
    extraction_result = ExtractionResult(
        doc_id="sample_property_doc",
        features={
            "owner_name": FeatureValue(
                value="Jane Doe",
                confidence=0.95,
                source_chunks=[
                    "The property is owned by Jane Doe.",
                    "Owner: Jane Doe, residing at 456 Oak Avenue",
                ],
                source_pages=[1],
            ),
            "sale_price": FeatureValue(
                value="$750,000",
                confidence=0.92,
                source_chunks=[
                    "Sale price: $750,000",
                    "The property was purchased for seven hundred fifty thousand dollars.",
                ],
                source_pages=[2],
            ),
            "lot_size": FeatureValue(
                value="1.2 acres",
                confidence=0.88,
                source_chunks=[
                    "Lot size: 1.2 acres",
                    "The parcel measures approximately 1.2 acres",
                ],
                source_pages=[1],
            ),
            "year_built": FeatureValue(
                value="1985",
                confidence=0.90,
                source_chunks=[
                    "Year built: 1985",
                    "Construction completed in 1985",
                ],
                source_pages=[3],
            ),
        },
        processing_time=8.5,
        metadata={
            "model": "gpt-4",
            "temperature": 0.0,
            "top_k": 5,
        },
    )
    print("   ✓ Extraction result created with 4 features")
    
    # Evaluate without ground truth
    print("\n3. Evaluating extraction quality (without ground truth)...")
    metrics = evaluator.evaluate(extraction_result)
    
    print(f"\n   RAGAS Metrics:")
    print(f"   - Faithfulness:       {metrics.faithfulness:.3f}")
    print(f"   - Answer Relevance:   {metrics.answer_relevance:.3f}")
    print(f"   - Context Precision:  {metrics.context_precision:.3f}")
    print(f"   - Context Recall:     {metrics.context_recall:.3f}")
    print(f"   - Overall Score:      {metrics.overall_score:.3f}")
    
    # Evaluate with ground truth
    print("\n4. Evaluating with ground truth data...")
    ground_truth = {
        "owner_name": "Jane Doe",
        "sale_price": "$750,000",
        "lot_size": "1.2 acres",
        "year_built": "1985",
    }
    
    metrics_with_gt = evaluator.evaluate(extraction_result, ground_truth)
    
    print(f"\n   RAGAS Metrics (with ground truth):")
    print(f"   - Faithfulness:       {metrics_with_gt.faithfulness:.3f}")
    print(f"   - Answer Relevance:   {metrics_with_gt.answer_relevance:.3f}")
    print(f"   - Context Precision:  {metrics_with_gt.context_precision:.3f}")
    print(f"   - Context Recall:     {metrics_with_gt.context_recall:.3f}")
    print(f"   - Overall Score:      {metrics_with_gt.overall_score:.3f}")
    
    # Test individual metric computation
    print("\n5. Testing individual metric computation...")
    
    answer = "The property is owned by Jane Doe"
    context = [
        "Owner: Jane Doe",
        "The property at 456 Oak Avenue is owned by Jane Doe",
    ]
    
    faithfulness = evaluator.compute_faithfulness(answer, context)
    print(f"   - Faithfulness for specific answer: {faithfulness:.3f}")
    
    question = "Who is the owner of the property?"
    answer = "Jane Doe"
    
    relevance = evaluator.compute_answer_relevance(question, answer)
    print(f"   - Answer relevance for specific Q&A: {relevance:.3f}")
    
    # Example with missing feature
    print("\n6. Testing with missing feature...")
    extraction_with_missing = ExtractionResult(
        doc_id="incomplete_doc",
        features={
            "owner_name": FeatureValue(
                value="Jane Doe",
                confidence=0.95,
                source_chunks=["Owner: Jane Doe"],
                source_pages=[1],
            ),
            "sale_price": FeatureValue(
                value=None,  # Missing feature
                confidence=0.0,
                source_chunks=[],
                source_pages=[],
            ),
        },
        processing_time=3.0,
        metadata={},
    )
    
    metrics_missing = evaluator.evaluate(extraction_with_missing)
    print(f"   - Overall score with missing feature: {metrics_missing.overall_score:.3f}")
    print("   ✓ Missing features handled gracefully")
    
    print("\n" + "=" * 60)
    print("✅ RAGAS Evaluator example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
