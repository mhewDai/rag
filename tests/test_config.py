"""Tests for configuration management system."""

import os
import json
import tempfile
import pytest
from pathlib import Path

from src.config import (
    Settings,
    OCRConfig,
    ChunkConfig,
    RAGConfig,
    VectorStoreConfig,
    PipelineConfig,
    APIConfig,
    LoggingConfig,
    ConfigurationManager,
    ConfigurationError,
    load_from_file,
    load_from_dict,
    create_default_config_file,
    merge_configs,
    validate_config_file,
)


def test_default_settings_creation():
    """Test that default settings can be created."""
    # Create settings with minimal API config
    settings = Settings(
        api=APIConfig(openai_api_key="test_key")
    )
    
    assert settings.ocr.dpi == 300
    assert settings.chunk.chunk_size == 800
    assert settings.rag.llm_model == "gpt-4"
    assert settings.pipeline.max_retries == 3


def test_ocr_config_validation():
    """Test OCR configuration validation."""
    # Valid config
    config = OCRConfig(dpi=300, language="eng")
    assert config.dpi == 300
    
    # Invalid DPI - too low
    with pytest.raises(ValueError):
        OCRConfig(dpi=50)
    
    # Invalid DPI - too high
    with pytest.raises(ValueError):
        OCRConfig(dpi=700)
    
    # Empty language
    with pytest.raises(ValueError):
        OCRConfig(language="")


def test_chunk_config_validation():
    """Test chunk configuration validation."""
    # Valid config
    config = ChunkConfig(chunk_size=800, chunk_overlap=100)
    assert config.chunk_size == 800
    
    # Invalid - overlap >= chunk_size
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=100, chunk_overlap=100)
    
    # Invalid - min_chunk_size > chunk_size
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=100, min_chunk_size=200)


def test_rag_config_validation():
    """Test RAG configuration validation."""
    # Valid config
    config = RAGConfig(llm_temperature=0.5)
    assert config.llm_temperature == 0.5
    
    # Invalid temperature - too high
    with pytest.raises(ValueError):
        RAGConfig(llm_temperature=3.0)
    
    # Invalid temperature - negative
    with pytest.raises(ValueError):
        RAGConfig(llm_temperature=-0.5)


def test_pipeline_config_validation():
    """Test pipeline configuration validation."""
    # Valid config
    config = PipelineConfig(max_retries=3)
    assert config.max_retries == 3
    
    # Invalid - too many retries
    with pytest.raises(ValueError):
        PipelineConfig(max_retries=15)


def test_api_config_validation():
    """Test API configuration validation."""
    # Valid - at least one key
    config = APIConfig(openai_api_key="test_key")
    assert config.openai_api_key == "test_key"
    
    # Invalid - no keys provided
    with pytest.raises(ValueError):
        APIConfig()


def test_configuration_manager_initialization():
    """Test configuration manager initialization."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "api": {"openai_api_key": "test_key"},
            "ocr": {"dpi": 300},
            "chunk": {"chunk_size": 1000}
        }
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(config_path=temp_path)
        settings = manager.get_settings()
        
        assert settings.chunk.chunk_size == 1000
        assert settings.ocr.dpi == 300
    finally:
        os.unlink(temp_path)


def test_runtime_configuration_override():
    """Test runtime configuration overrides."""
    # Create manager with default settings
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "api": {"openai_api_key": "test_key"},
            "chunk": {"chunk_size": 800}
        }
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(config_path=temp_path)
        
        # Apply runtime override
        overrides = {
            "chunk": {"chunk_size": 1200},
            "rag": {"llm_temperature": 0.7}
        }
        
        overridden_settings = manager.override_settings(overrides)
        
        # Check overrides applied
        assert overridden_settings.chunk.chunk_size == 1200
        assert overridden_settings.rag.llm_temperature == 0.7
        
        # Original settings unchanged
        original_settings = manager.get_settings()
        assert original_settings.chunk.chunk_size == 800
        assert original_settings.rag.llm_temperature == 0.0
    finally:
        os.unlink(temp_path)


def test_configuration_reload():
    """Test hot configuration reload."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "api": {"openai_api_key": "test_key"},
            "chunk": {"chunk_size": 800}
        }
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(config_path=temp_path)
        settings = manager.get_settings()
        assert settings.chunk.chunk_size == 800
        
        # Modify the config file
        with open(temp_path, 'w') as f:
            config_dict["chunk"]["chunk_size"] = 1000
            json.dump(config_dict, f)
        
        # Reload configuration
        manager.reload_configuration()
        settings = manager.get_settings()
        
        # Check new value loaded
        assert settings.chunk.chunk_size == 1000
    finally:
        os.unlink(temp_path)


def test_load_from_dict():
    """Test loading configuration from dictionary."""
    config_dict = {
        "api": {"openai_api_key": "test_key"},
        "ocr": {"dpi": 350},
        "chunk": {"chunk_size": 900}
    }
    
    settings = load_from_dict(config_dict)
    
    assert settings.ocr.dpi == 350
    assert settings.chunk.chunk_size == 900


def test_merge_configs():
    """Test merging configurations."""
    base = Settings(api=APIConfig(openai_api_key="test_key"))
    
    overrides = {
        "chunk": {"chunk_size": 1200},
        "rag": {"top_k_retrieval": 10}
    }
    
    merged = merge_configs(base, overrides)
    
    assert merged.chunk.chunk_size == 1200
    assert merged.rag.top_k_retrieval == 10
    # Base values preserved
    assert merged.ocr.dpi == 300


def test_validate_config_file():
    """Test configuration file validation."""
    # Valid config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "api": {"openai_api_key": "test_key"},
            "chunk": {"chunk_size": 800}
        }
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        is_valid, errors = validate_config_file(temp_path)
        assert is_valid
        assert len(errors) == 0
    finally:
        os.unlink(temp_path)
    
    # Invalid config file - bad JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        is_valid, errors = validate_config_file(temp_path)
        assert not is_valid
        assert len(errors) > 0
    finally:
        os.unlink(temp_path)


def test_create_default_config_file():
    """Test creating default configuration file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        create_default_config_file(temp_path)
        
        # Verify file was created and is valid
        assert os.path.exists(temp_path)
        
        with open(temp_path, 'r') as f:
            config_dict = json.load(f)
        
        assert "ocr" in config_dict
        assert "chunk" in config_dict
        assert "rag" in config_dict
        assert "pipeline" in config_dict
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_configuration_validation():
    """Test configuration validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "api": {"openai_api_key": "test_key"},
            "logging": {"log_file": "./logs/test.log"}
        }
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(config_path=temp_path)
        errors = manager.validate_configuration()
        
        # Should have no errors or only directory-related warnings
        assert isinstance(errors, list)
    finally:
        os.unlink(temp_path)


def test_invalid_configuration_error():
    """Test that invalid configuration raises appropriate errors."""
    # Invalid config - missing required API key
    with pytest.raises(ValueError):
        Settings(api=APIConfig())
    
    # Invalid config - bad chunk overlap
    with pytest.raises(ValueError):
        Settings(
            api=APIConfig(openai_api_key="test"),
            chunk=ChunkConfig(chunk_size=100, chunk_overlap=200)
        )
