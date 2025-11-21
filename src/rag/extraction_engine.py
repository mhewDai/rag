"""RAG-based extraction engine for property features.

This module implements the RAG (Retrieval-Augmented Generation) extraction engine
that extracts property features from documents using semantic search and LLM generation.
"""

import time
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from openai import OpenAI
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models.feature_models import (
    FeatureDefinition,
    FeatureValue,
    ExtractionResult,
)
from src.vector_store.vector_store import VectorStore, SearchResult
from src.config.settings import RAGConfig


class RAGExtractionEngine:
    """
    RAG-based extraction engine for property features.
    
    This engine uses retrieval-augmented generation to extract property features
    from documents. It retrieves relevant chunks from a vector store and uses
    an LLM to generate accurate extractions with confidence scores and source attribution.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        config: RAGConfig,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize RAG extraction engine.
        
        Args:
            vector_store: Vector store for semantic search
            config: RAG configuration
            openai_api_key: Optional OpenAI API key
            anthropic_api_key: Optional Anthropic API key
            
        Raises:
            ValueError: If no API keys are provided
        """
        self.vector_store = vector_store
        self.config = config
        
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        
        if anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        
        if not self.openai_client and not self.anthropic_client:
            raise ValueError("At least one API key (OpenAI or Anthropic) must be provided")
        
        # Determine which client to use based on model name
        self._use_openai = self._should_use_openai(config.llm_model)
    
    def _should_use_openai(self, model_name: str) -> bool:
        """
        Determine if we should use OpenAI based on model name.
        
        Args:
            model_name: Name of the LLM model
            
        Returns:
            True if OpenAI should be used, False for Anthropic
        """
        openai_models = ["gpt-3.5", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        return any(model in model_name.lower() for model in openai_models)
    
    def extract_features(
        self,
        doc_id: str,
        feature_schema: Dict[str, FeatureDefinition],
    ) -> ExtractionResult:
        """
        Extract all features from a document using RAG.
        
        Args:
            doc_id: Document identifier in vector store
            feature_schema: Dictionary mapping feature names to their definitions
            
        Returns:
            ExtractionResult with extracted values, confidence, and sources
            
        Raises:
            ValueError: If document not found in vector store
        """
        start_time = time.time()
        
        # Verify document exists
        if not self.vector_store.document_exists(doc_id):
            raise ValueError(f"Document {doc_id} not found in vector store")
        
        # Extract each feature
        features: Dict[str, FeatureValue] = {}
        
        for feature_name, feature_def in feature_schema.items():
            try:
                feature_value = self.extract_single_feature(doc_id, feature_def)
                features[feature_name] = feature_value
            except Exception as e:
                # Handle missing features gracefully with null values
                features[feature_name] = FeatureValue(
                    value=None,
                    confidence=0.0,
                    source_chunks=[],
                    source_pages=[],
                )
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            doc_id=doc_id,
            features=features,
            processing_time=processing_time,
            metadata={
                "model": self.config.llm_model,
                "temperature": self.config.llm_temperature,
                "top_k": self.config.top_k_retrieval,
            },
        )
    
    def extract_single_feature(
        self,
        doc_id: str,
        feature: FeatureDefinition,
    ) -> FeatureValue:
        """
        Extract a single feature with retrieval context.
        
        Args:
            doc_id: Document identifier in vector store
            feature: Feature definition to extract
            
        Returns:
            FeatureValue with extracted value, confidence, and sources
        """
        # Generate feature-specific query
        query = self._generate_query(feature)
        
        # Retrieve relevant chunks
        search_results = self.vector_store.search(
            query=query,
            top_k=self.config.top_k_retrieval,
            doc_id=doc_id,
        )
        
        # If no chunks retrieved, return null value
        if not search_results:
            return FeatureValue(
                value=None,
                confidence=0.0,
                source_chunks=[],
                source_pages=[],
            )
        
        # Extract chunks and metadata
        chunks = [result.chunk for result in search_results]
        chunk_texts = [chunk.text for chunk in chunks]
        source_pages = list(set(chunk.page_number for chunk in chunks))
        
        # Generate extraction using LLM
        extraction_response = self._generate_extraction(
            feature=feature,
            context_chunks=chunk_texts,
        )
        
        # Parse response
        value, confidence = self._parse_extraction_response(
            extraction_response,
            feature,
        )
        
        return FeatureValue(
            value=value,
            confidence=confidence,
            source_chunks=chunk_texts,
            source_pages=sorted(source_pages),
        )
    
    def _generate_query(self, feature: FeatureDefinition) -> str:
        """
        Generate a feature-specific query for retrieval.
        
        Args:
            feature: Feature definition
            
        Returns:
            Query string optimized for semantic search
        """
        # Create a query that combines feature name and description
        query_parts = [
            feature.name.replace("_", " "),
            feature.description,
        ]
        
        # Add data type hints for better retrieval
        if feature.data_type == "currency":
            query_parts.append("price amount dollar")
        elif feature.data_type == "date":
            query_parts.append("date year month day")
        elif feature.data_type == "number":
            query_parts.append("number count quantity")
        
        return " ".join(query_parts)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _generate_extraction(
        self,
        feature: FeatureDefinition,
        context_chunks: List[str],
    ) -> str:
        """
        Generate extraction using LLM with retry logic.
        
        Args:
            feature: Feature definition
            context_chunks: Retrieved context chunks
            
        Returns:
            LLM response as string
        """
        # Build prompt
        prompt = self._build_extraction_prompt(feature, context_chunks)
        
        # Call appropriate LLM
        if self._use_openai and self.openai_client:
            return self._call_openai(prompt)
        elif self.anthropic_client:
            return self._call_anthropic(prompt)
        else:
            raise ValueError("No LLM client available")
    
    def _build_extraction_prompt(
        self,
        feature: FeatureDefinition,
        context_chunks: List[str],
    ) -> str:
        """
        Build extraction prompt for LLM.
        
        Args:
            feature: Feature definition
            context_chunks: Retrieved context chunks
            
        Returns:
            Formatted prompt string
        """
        context = "\n\n".join(
            f"[Chunk {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        )
        
        prompt = f"""You are extracting property information from documents.

Feature to extract: {feature.name}
Description: {feature.description}
Data type: {feature.data_type}
Required: {feature.required}

Extraction instructions:
{feature.extraction_prompt}

Context from document:
{context}

Please extract the requested feature from the context above. Respond in JSON format with the following structure:
{{
    "value": <extracted value or null if not found>,
    "confidence": <confidence score between 0.0 and 1.0>,
    "reasoning": <brief explanation of your extraction>
}}

Important:
- If the feature is not found in the context, return null for value and 0.0 for confidence
- Do not hallucinate or make up information
- Base your extraction only on the provided context
- Provide a confidence score based on how clearly the information appears in the context
- For currency values, include the dollar sign (e.g., "$500,000")
- For dates, use a standard format (MM/DD/YYYY or YYYY-MM-DD)
- For numbers, return only the numeric value

Respond only with the JSON object, no additional text."""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            Response text
        """
        response = self.openai_client.chat.completions.create(
            model=self.config.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise property data extraction assistant. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.llm_temperature,
            max_tokens=self.config.max_tokens,
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """
        Call Anthropic API.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            Response text
        """
        response = self.anthropic_client.messages.create(
            model=self.config.llm_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.llm_temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        return response.content[0].text
    
    def _parse_extraction_response(
        self,
        response: str,
        feature: FeatureDefinition,
    ) -> tuple[Any, float]:
        """
        Parse LLM extraction response.
        
        Args:
            response: LLM response string
            feature: Feature definition
            
        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        try:
            # Try to parse as JSON
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                # Extract JSON from code block
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
                if match:
                    response = match.group(1)
                else:
                    # Try to remove just the backticks
                    response = response.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(response)
            
            value = data.get("value")
            confidence = float(data.get("confidence", 0.0))
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            # Apply confidence threshold
            if confidence < self.config.confidence_threshold:
                return None, confidence
            
            # Convert value based on data type
            if value is not None:
                value = self._convert_value_type(value, feature.data_type)
            
            return value, confidence
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # If parsing fails, return null with low confidence
            return None, 0.0
    
    def _convert_value_type(self, value: Any, data_type: str) -> Any:
        """
        Convert extracted value to appropriate type.
        
        Args:
            value: Raw extracted value
            data_type: Target data type
            
        Returns:
            Converted value
        """
        if value is None:
            return None
        
        try:
            if data_type == "number":
                # Try to convert to int first, then float
                if isinstance(value, str):
                    # Remove commas from numbers
                    value = value.replace(",", "")
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            
            elif data_type == "string":
                return str(value)
            
            elif data_type in ["currency", "date"]:
                # Keep as string for currency and dates
                return str(value)
            
            else:
                return value
                
        except (ValueError, TypeError):
            # If conversion fails, return as string
            return str(value)
