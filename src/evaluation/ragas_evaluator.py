"""RAGAS evaluation module for RAG system quality assessment.

This module implements the RAGASEvaluator class that computes quality metrics
for the RAG extraction system using the RAGAS framework.
"""

import time
from typing import List, Optional, Dict, Any

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

from src.models.evaluation_models import RAGASMetrics
from src.models.feature_models import ExtractionResult, FeatureValue


class RAGASEvaluator:
    """
    RAGAS evaluator for RAG system quality assessment.
    
    This evaluator computes RAGAS metrics including faithfulness, answer relevance,
    context precision, and context recall to measure the quality of RAG-based
    feature extraction.
    """
    
    def __init__(self, llm_api_key: Optional[str] = None):
        """
        Initialize RAGAS evaluator.
        
        Args:
            llm_api_key: Optional API key for LLM used in RAGAS metrics
        """
        self.llm_api_key = llm_api_key
        
        # Initialize RAGAS metrics
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ]
    
    def evaluate(
        self,
        extraction_result: ExtractionResult,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> RAGASMetrics:
        """
        Compute RAGAS metrics for extraction result.
        
        Args:
            extraction_result: Results from RAG extraction
            ground_truth: Optional validated data for comparison
            
        Returns:
            RAGASMetrics with scores for each metric
        """
        # Prepare data for RAGAS evaluation
        dataset = self._prepare_dataset(extraction_result, ground_truth)
        
        # If dataset is empty, return zero metrics
        if not dataset or len(dataset["question"]) == 0:
            return RAGASMetrics(
                faithfulness=0.0,
                answer_relevance=0.0,
                context_precision=0.0,
                context_recall=0.0,
                overall_score=0.0,
            )
        
        # Convert to RAGAS dataset format
        ragas_dataset = Dataset.from_dict(dataset)
        
        # Evaluate using RAGAS
        try:
            results = evaluate(
                dataset=ragas_dataset,
                metrics=self.metrics,
            )
            
            # Extract individual metric scores
            faithfulness_score = float(results.get("faithfulness", 0.0))
            answer_relevance_score = float(results.get("answer_relevancy", 0.0))
            context_precision_score = float(results.get("context_precision", 0.0))
            context_recall_score = float(results.get("context_recall", 0.0))
            
            # Compute overall score as average
            overall_score = (
                faithfulness_score +
                answer_relevance_score +
                context_precision_score +
                context_recall_score
            ) / 4.0
            
            return RAGASMetrics(
                faithfulness=faithfulness_score,
                answer_relevance=answer_relevance_score,
                context_precision=context_precision_score,
                context_recall=context_recall_score,
                overall_score=overall_score,
            )
            
        except Exception as e:
            # If RAGAS evaluation fails, return zero metrics
            # This can happen if API keys are not configured or other issues
            return RAGASMetrics(
                faithfulness=0.0,
                answer_relevance=0.0,
                context_precision=0.0,
                context_recall=0.0,
                overall_score=0.0,
            )
    
    def compute_faithfulness(
        self,
        answer: str,
        context: List[str],
    ) -> float:
        """
        Check if answer is supported by context.
        
        Faithfulness measures whether the extracted answer is grounded in
        the retrieved context chunks.
        
        Args:
            answer: Extracted answer/value
            context: List of context chunks
            
        Returns:
            Faithfulness score between 0.0 and 1.0
        """
        # Prepare single-item dataset
        dataset = Dataset.from_dict({
            "question": ["Extract the information"],
            "answer": [answer],
            "contexts": [context],
        })
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=[faithfulness],
            )
            return float(results.get("faithfulness", 0.0))
        except Exception:
            return 0.0
    
    def compute_answer_relevance(
        self,
        question: str,
        answer: str,
    ) -> float:
        """
        Check if answer addresses the question.
        
        Answer relevance measures whether the extracted value actually
        answers the feature extraction query.
        
        Args:
            question: Feature extraction query
            answer: Extracted answer/value
            
        Returns:
            Answer relevance score between 0.0 and 1.0
        """
        # Prepare single-item dataset
        # Need dummy contexts for RAGAS
        dataset = Dataset.from_dict({
            "question": [question],
            "answer": [answer],
            "contexts": [["dummy context"]],
        })
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=[answer_relevancy],
            )
            return float(results.get("answer_relevancy", 0.0))
        except Exception:
            return 0.0
    
    def compute_context_precision(
        self,
        question: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> float:
        """
        Measure whether retrieved chunks contain relevant information.
        
        Context precision measures the proportion of retrieved chunks
        that are actually relevant to answering the question.
        
        Args:
            question: Feature extraction query
            contexts: Retrieved context chunks
            ground_truth: Optional ground truth answer
            
        Returns:
            Context precision score between 0.0 and 1.0
        """
        # Context precision requires ground truth
        if not ground_truth:
            return 0.0
        
        # Prepare single-item dataset
        dataset = Dataset.from_dict({
            "question": [question],
            "contexts": [contexts],
            "ground_truth": [ground_truth],
        })
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=[context_precision],
            )
            return float(results.get("context_precision", 0.0))
        except Exception:
            return 0.0
    
    def compute_context_recall(
        self,
        contexts: List[str],
        ground_truth: str,
    ) -> float:
        """
        Measure whether all relevant information was retrieved.
        
        Context recall measures whether the retrieved chunks contain
        all the information needed to answer the question correctly.
        
        Args:
            contexts: Retrieved context chunks
            ground_truth: Ground truth answer
            
        Returns:
            Context recall score between 0.0 and 1.0
        """
        # Prepare single-item dataset
        # Need dummy question for RAGAS
        dataset = Dataset.from_dict({
            "question": ["Extract the information"],
            "contexts": [contexts],
            "ground_truth": [ground_truth],
        })
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=[context_recall],
            )
            return float(results.get("context_recall", 0.0))
        except Exception:
            return 0.0
    
    def _prepare_dataset(
        self,
        extraction_result: ExtractionResult,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Any]]:
        """
        Prepare dataset for RAGAS evaluation.
        
        Args:
            extraction_result: Extraction result to evaluate
            ground_truth: Optional ground truth data
            
        Returns:
            Dictionary with lists for question, answer, contexts, ground_truth
        """
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        
        # Process each extracted feature
        for feature_name, feature_value in extraction_result.features.items():
            # Skip features with no value
            if feature_value.value is None:
                continue
            
            # Create question from feature name
            question = f"What is the {feature_name.replace('_', ' ')}?"
            questions.append(question)
            
            # Convert answer to string
            answer = str(feature_value.value)
            answers.append(answer)
            
            # Use source chunks as contexts
            feature_contexts = feature_value.source_chunks
            if not feature_contexts:
                feature_contexts = ["No context available"]
            contexts.append(feature_contexts)
            
            # Add ground truth if available
            if ground_truth and feature_name in ground_truth:
                ground_truths.append(str(ground_truth[feature_name]))
            else:
                # Use extracted value as ground truth if not provided
                ground_truths.append(answer)
        
        return {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
