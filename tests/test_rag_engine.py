"""Unit tests for RAG extraction engine."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.rag.extraction_engine import RAGExtractionEngine
from src.models.feature_models import FeatureDefinition, ValidationRule, FeatureValue
from src.models.chunk_models import Chunk
from src.vector_store.vector_store import SearchResult
from src.config.settings import RAGConfig


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock()
    store.document_exists.return_value = True
    return store


@pytest.fixture
def rag_config():
    """Create RAG configuration."""
    return RAGConfig(
        llm_model="gpt-4",
        llm_temperature=0.0,
        top_k_retrieval=3,
        confidence_threshold=0.5,
    )


@pytest.fixture
def sample_feature():
    """Create a sample feature definition."""
    return FeatureDefinition(
        name="owner_name",
        description="The name of the property owner",
        data_type="string",
        required=True,
        extraction_prompt="Extract the property owner's name from the document.",
        validation_rules=[],
    )


@pytest.fixture
def sample_chunks():
    """Create sample chunks."""
    return [
        Chunk(
            text="Property Owner: John Smith",
            chunk_id="chunk_1",
            doc_id="doc_1",
            page_number=1,
            start_pos=0,
            end_pos=27,
        ),
        Chunk(
            text="The property is owned by John Smith",
            chunk_id="chunk_2",
            doc_id="doc_1",
            page_number=1,
            start_pos=28,
            end_pos=64,
        ),
    ]


def test_rag_engine_initialization_with_openai():
    """Test RAG engine initialization with OpenAI."""
    mock_store = Mock()
    config = RAGConfig()
    
    engine = RAGExtractionEngine(
        vector_store=mock_store,
        config=config,
        openai_api_key="test_key",
    )
    
    assert engine.vector_store == mock_store
    assert engine.config == config
    assert engine.openai_client is not None


def test_rag_engine_initialization_with_anthropic():
    """Test RAG engine initialization with Anthropic."""
    mock_store = Mock()
    config = RAGConfig()
    
    engine = RAGExtractionEngine(
        vector_store=mock_store,
        config=config,
        anthropic_api_key="test_key",
    )
    
    assert engine.vector_store == mock_store
    assert engine.config == config
    assert engine.anthropic_client is not None


def test_rag_engine_initialization_without_api_keys():
    """Test RAG engine initialization fails without API keys."""
    mock_store = Mock()
    config = RAGConfig()
    
    with pytest.raises(ValueError, match="At least one API key"):
        RAGExtractionEngine(
            vector_store=mock_store,
            config=config,
        )


def test_should_use_openai():
    """Test model selection logic."""
    mock_store = Mock()
    config = RAGConfig()
    
    engine = RAGExtractionEngine(
        vector_store=mock_store,
        config=config,
        openai_api_key="test_key",
    )
    
    assert engine._should_use_openai("gpt-4") is True
    assert engine._should_use_openai("gpt-3.5-turbo") is True
    assert engine._should_use_openai("claude-3") is False


def test_generate_query(mock_vector_store, rag_config, sample_feature):
    """Test query generation for feature extraction."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    query = engine._generate_query(sample_feature)
    
    assert "owner name" in query.lower()
    assert "property owner" in query.lower()


def test_generate_query_with_currency_type(mock_vector_store, rag_config):
    """Test query generation includes type hints for currency."""
    feature = FeatureDefinition(
        name="sale_price",
        description="The sale price",
        data_type="currency",
        required=False,
        extraction_prompt="Extract the sale price",
        validation_rules=[],
    )
    
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    query = engine._generate_query(feature)
    
    assert "price" in query.lower() or "dollar" in query.lower()


def test_convert_value_type_number(mock_vector_store, rag_config):
    """Test value type conversion for numbers."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    # Test integer conversion
    assert engine._convert_value_type("42", "number") == 42
    assert engine._convert_value_type("1,234", "number") == 1234
    
    # Test float conversion
    assert engine._convert_value_type("3.14", "number") == 3.14


def test_convert_value_type_string(mock_vector_store, rag_config):
    """Test value type conversion for strings."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    assert engine._convert_value_type(123, "string") == "123"
    assert engine._convert_value_type("test", "string") == "test"


def test_convert_value_type_none(mock_vector_store, rag_config):
    """Test value type conversion handles None."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    assert engine._convert_value_type(None, "string") is None
    assert engine._convert_value_type(None, "number") is None


def test_parse_extraction_response_valid_json(mock_vector_store, rag_config, sample_feature):
    """Test parsing valid JSON extraction response."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    response = '{"value": "John Smith", "confidence": 0.95, "reasoning": "Found in document"}'
    value, confidence = engine._parse_extraction_response(response, sample_feature)
    
    assert value == "John Smith"
    assert confidence == 0.95


def test_parse_extraction_response_with_markdown(mock_vector_store, rag_config, sample_feature):
    """Test parsing JSON wrapped in markdown code blocks."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    response = '```json\n{"value": "John Smith", "confidence": 0.95}\n```'
    value, confidence = engine._parse_extraction_response(response, sample_feature)
    
    assert value == "John Smith"
    assert confidence == 0.95


def test_parse_extraction_response_low_confidence(mock_vector_store, rag_config, sample_feature):
    """Test parsing response with confidence below threshold."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    response = '{"value": "John Smith", "confidence": 0.3}'
    value, confidence = engine._parse_extraction_response(response, sample_feature)
    
    # Value should be None due to low confidence
    assert value is None
    assert confidence == 0.3


def test_parse_extraction_response_null_value(mock_vector_store, rag_config, sample_feature):
    """Test parsing response with null value."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    response = '{"value": null, "confidence": 0.0}'
    value, confidence = engine._parse_extraction_response(response, sample_feature)
    
    assert value is None
    assert confidence == 0.0


def test_parse_extraction_response_invalid_json(mock_vector_store, rag_config, sample_feature):
    """Test parsing invalid JSON returns null."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    response = 'This is not valid JSON'
    value, confidence = engine._parse_extraction_response(response, sample_feature)
    
    assert value is None
    assert confidence == 0.0


def test_build_extraction_prompt(mock_vector_store, rag_config, sample_feature):
    """Test extraction prompt building."""
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    chunks = ["Property Owner: John Smith", "Located at 123 Main St"]
    prompt = engine._build_extraction_prompt(sample_feature, chunks)
    
    assert "owner_name" in prompt
    assert "Property Owner: John Smith" in prompt
    assert "JSON" in prompt
    assert "confidence" in prompt


def test_extract_features_document_not_found(mock_vector_store, rag_config):
    """Test extraction fails gracefully when document not found."""
    mock_vector_store.document_exists.return_value = False
    
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    feature_schema = {
        "owner_name": FeatureDefinition(
            name="owner_name",
            description="Owner name",
            data_type="string",
            required=True,
            extraction_prompt="Extract owner",
            validation_rules=[],
        )
    }
    
    with pytest.raises(ValueError, match="not found in vector store"):
        engine.extract_features("nonexistent_doc", feature_schema)


def test_extract_single_feature_no_chunks_found(mock_vector_store, rag_config, sample_feature):
    """Test extraction returns null when no chunks are retrieved."""
    mock_vector_store.search.return_value = []
    
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    result = engine.extract_single_feature("doc_1", sample_feature)
    
    assert result.value is None
    assert result.confidence == 0.0
    assert result.source_chunks == []
    assert result.source_pages == []


def test_extract_single_feature_with_chunks(mock_vector_store, rag_config, sample_feature, sample_chunks):
    """Test extraction with retrieved chunks."""
    # Mock search results
    search_results = [
        SearchResult(chunk=chunk, score=0.9, metadata={})
        for chunk in sample_chunks
    ]
    mock_vector_store.search.return_value = search_results
    
    engine = RAGExtractionEngine(
        vector_store=mock_vector_store,
        config=rag_config,
        openai_api_key="test_key",
    )
    
    # Mock LLM response
    with patch.object(engine, '_generate_extraction') as mock_generate:
        mock_generate.return_value = '{"value": "John Smith", "confidence": 0.95}'
        
        result = engine.extract_single_feature("doc_1", sample_feature)
        
        assert result.value == "John Smith"
        assert result.confidence == 0.95
        assert len(result.source_chunks) == 2
        assert result.source_pages == [1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
