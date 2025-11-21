# RAGAS Evaluator Module

## Overview

The RAGAS Evaluator module provides quality assessment for the RAG (Retrieval-Augmented Generation) extraction system using the RAGAS (RAG Assessment) framework. It computes multiple metrics to measure the quality and reliability of feature extraction.

## Features

- **Faithfulness**: Measures whether extracted values are grounded in source text
- **Answer Relevance**: Measures whether extracted values match requested features
- **Context Precision**: Measures whether retrieved chunks contain relevant information
- **Context Recall**: Measures whether all relevant information was retrieved
- **Overall Score**: Aggregated quality metric across all dimensions

## Architecture

```
ExtractionResult → RAGASEvaluator → RAGASMetrics
                         ↓
                   RAGAS Library
                   (faithfulness, answer_relevancy,
                    context_precision, context_recall)
```

## Components

### RAGASEvaluator

Main class for computing RAGAS metrics.

**Methods:**

- `evaluate(extraction_result, ground_truth=None)`: Compute all RAGAS metrics for an extraction result
- `compute_faithfulness(answer, context)`: Compute faithfulness score for a single answer
- `compute_answer_relevance(question, answer)`: Compute answer relevance score
- `compute_context_precision(question, contexts, ground_truth)`: Compute context precision
- `compute_context_recall(contexts, ground_truth)`: Compute context recall

### RAGASMetrics

Data model for RAGAS evaluation results.

**Fields:**

- `faithfulness`: Score between 0.0 and 1.0
- `answer_relevance`: Score between 0.0 and 1.0
- `context_precision`: Score between 0.0 and 1.0
- `context_recall`: Score between 0.0 and 1.0
- `overall_score`: Average of all metrics

## Usage

### Basic Evaluation

```python
from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.models.feature_models import ExtractionResult

# Initialize evaluator
evaluator = RAGASEvaluator()

# Evaluate extraction result
metrics = evaluator.evaluate(extraction_result)

print(f"Faithfulness: {metrics.faithfulness:.3f}")
print(f"Answer Relevance: {metrics.answer_relevance:.3f}")
print(f"Context Precision: {metrics.context_precision:.3f}")
print(f"Context Recall: {metrics.context_recall:.3f}")
print(f"Overall Score: {metrics.overall_score:.3f}")
```

### Evaluation with Ground Truth

```python
# Define ground truth data
ground_truth = {
    "owner_name": "John Smith",
    "sale_price": "$500,000",
    "lot_size": "0.5 acres",
}

# Evaluate with ground truth
metrics = evaluator.evaluate(extraction_result, ground_truth)
```

### Individual Metric Computation

```python
# Compute faithfulness
answer = "The property is owned by John Smith"
context = ["Owner: John Smith", "Property at 123 Main St"]
faithfulness = evaluator.compute_faithfulness(answer, context)

# Compute answer relevance
question = "Who is the owner?"
answer = "John Smith"
relevance = evaluator.compute_answer_relevance(question, answer)

# Compute context precision (requires ground truth)
question = "What is the sale price?"
contexts = ["Sale price: $500,000"]
ground_truth = "$500,000"
precision = evaluator.compute_context_precision(question, contexts, ground_truth)

# Compute context recall
contexts = ["Sale price: $500,000"]
ground_truth = "$500,000"
recall = evaluator.compute_context_recall(contexts, ground_truth)
```

## RAGAS Metrics Explained

### Faithfulness

Measures whether the extracted answer is supported by the retrieved context chunks. A high faithfulness score indicates that the extraction is grounded in the source document and not hallucinated.

**Score Range**: 0.0 (not faithful) to 1.0 (fully faithful)

**Example:**
- Context: "Owner: John Smith"
- Answer: "John Smith" → High faithfulness
- Answer: "Jane Doe" → Low faithfulness

### Answer Relevance

Measures whether the extracted value actually answers the feature extraction query. A high relevance score indicates that the extraction is on-topic and addresses the requested feature.

**Score Range**: 0.0 (not relevant) to 1.0 (highly relevant)

**Example:**
- Question: "What is the sale price?"
- Answer: "$500,000" → High relevance
- Answer: "John Smith" → Low relevance

### Context Precision

Measures the proportion of retrieved chunks that are actually relevant to answering the question. A high precision score indicates that the retrieval system is returning focused, relevant content.

**Score Range**: 0.0 (no relevant chunks) to 1.0 (all chunks relevant)

**Requires**: Ground truth data

**Example:**
- Question: "What is the sale price?"
- Contexts: ["Sale price: $500,000", "Owner: John Smith"]
- Ground Truth: "$500,000"
- Precision: 0.5 (1 out of 2 chunks relevant)

### Context Recall

Measures whether all relevant information needed to answer the question was retrieved. A high recall score indicates that the retrieval system is not missing important context.

**Score Range**: 0.0 (missing all relevant info) to 1.0 (retrieved all relevant info)

**Requires**: Ground truth data

**Example:**
- Ground Truth: "$500,000 sold on January 15, 2023"
- Contexts: ["Sale price: $500,000"]
- Recall: 0.5 (retrieved price but not date)

### Overall Score

The average of all four metrics, providing a single quality indicator for the RAG system.

**Score Range**: 0.0 (poor quality) to 1.0 (excellent quality)

## Error Handling

The evaluator handles various error conditions gracefully:

- **Empty Extraction Results**: Returns zero metrics
- **Null Feature Values**: Skips null values in evaluation
- **Missing Contexts**: Provides default context when chunks are empty
- **API Failures**: Returns zero metrics if RAGAS library fails
- **Missing Ground Truth**: Uses extracted values as ground truth when not provided

## Integration with Pipeline

The RAGAS evaluator integrates with the extraction pipeline:

```python
from src.pipeline.extraction_pipeline import ExtractionPipeline
from src.evaluation.ragas_evaluator import RAGASEvaluator

# Initialize pipeline and evaluator
pipeline = ExtractionPipeline(config)
evaluator = RAGASEvaluator()

# Process document
extraction_result = pipeline.extract_features(pdf_path)

# Evaluate quality
metrics = evaluator.evaluate(extraction_result)

# Create pipeline result with metrics
pipeline_result = PipelineResult(
    doc_id=extraction_result.doc_id,
    extraction=extraction_result,
    ragas_metrics=metrics,
    errors=[],
    success=True,
)
```

## Performance Considerations

- **API Calls**: RAGAS metrics may require LLM API calls for evaluation
- **Batch Evaluation**: Evaluate multiple documents in parallel for efficiency
- **Caching**: Consider caching metric results for repeated evaluations
- **Timeouts**: Set appropriate timeouts for RAGAS library calls

## Dependencies

- `ragas>=0.1.0`: RAGAS framework for RAG evaluation
- `datasets`: Required by RAGAS for data handling
- `langchain`: Required by RAGAS for LLM integration

## Testing

Run unit tests:

```bash
pytest tests/test_ragas_evaluator.py -v
```

Run verification script:

```bash
python verify_ragas_evaluator.py
```

Run example:

```bash
python examples/ragas_evaluator_usage.py
```

## Configuration

The evaluator can be configured with an LLM API key for metric computation:

```python
evaluator = RAGASEvaluator(llm_api_key="your-api-key")
```

If no API key is provided, the evaluator will attempt to use environment variables or return zero metrics if evaluation fails.

## Best Practices

1. **Always Evaluate**: Run RAGAS evaluation on all extractions to monitor quality
2. **Use Ground Truth**: Provide ground truth data when available for more accurate metrics
3. **Monitor Trends**: Track metrics over time to identify quality degradation
4. **Set Thresholds**: Define minimum acceptable scores for each metric
5. **Investigate Low Scores**: Review extractions with low scores for improvement opportunities

## Troubleshooting

### Zero Metrics

If all metrics return 0.0:
- Check that extraction result contains non-null features
- Verify RAGAS library is installed correctly
- Ensure API keys are configured if required
- Check for exceptions in logs

### Low Faithfulness

If faithfulness scores are low:
- Review retrieved context chunks for relevance
- Adjust retrieval parameters (top_k, similarity threshold)
- Improve chunking strategy for better context

### Low Context Precision/Recall

If context metrics are low:
- Tune vector store retrieval parameters
- Improve embedding model quality
- Adjust chunk size and overlap
- Refine feature-specific queries

## Future Enhancements

- Support for custom RAGAS metrics
- Batch evaluation optimization
- Metric caching and persistence
- Real-time monitoring dashboard
- Automated quality alerts
